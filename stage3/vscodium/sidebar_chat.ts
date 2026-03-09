// APEX Sidebar Chat Provider - VSCode Sidebar View

import * as vscode from 'vscode';
import { IntelligenceClient } from './intelligence_client';

export class SidebarChatProvider implements vscode.WebviewViewProvider {
    public static readonly viewType = 'apex.chatSidebar';

    private _view?: vscode.WebviewView;
    private _intelligenceClient: IntelligenceClient;
    private _messages: Array<{ role: 'user' | 'assistant'; content: string }> = [];
    private _workspaceContext: string = '';
    private _tokenManifest: any = null;
    private _currentContextTokens: number = 0;
    private readonly MAX_CONTEXT_TOKENS: number = 32768;
    private _archetypeData: any = null;
    private _projectArchetype: string = 'Unknown';

    constructor(
        private readonly _extensionUri: vscode.Uri,
        client: IntelligenceClient
    ) {
        this._intelligenceClient = client;
        this._buildWorkspaceContext();
        this._loadTokenManifest();
        this._detectArchetype();
    }

    public resolveWebviewView(
        webviewView: vscode.WebviewView,
        context: vscode.WebviewViewResolveContext,
        _token: vscode.CancellationToken
    ) {
        this._view = webviewView;

        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [this._extensionUri]
        };

        webviewView.webview.html = this._getHtmlForWebview(webviewView.webview);

        // Handle messages from webview
        webviewView.webview.onDidReceiveMessage(async (message) => {
            switch (message.command) {
                case 'sendMessage':
                    await this._handleUserMessage(message.text, message.selectedCode);
                    break;
                case 'clearChat':
                    this._messages = [];
                    webviewView.webview.postMessage({ command: 'clearChat' });
                    break;
                case 'getWorkspaceInfo':
                    webviewView.webview.postMessage({
                        command: 'workspaceInfo',
                        workspace: this._workspaceContext
                    });
                    break;
            }
        });

        // Listen for editor selection changes
        vscode.window.onDidChangeTextEditorSelection((e) => {
            if (!e.selections[0].isEmpty) {
                const selectedCode = e.textEditor.document.getText(e.selections[0]);
                this._view?.webview.postMessage({
                    command: 'selectionChanged',
                    file: e.textEditor.document.fileName,
                    selection: selectedCode,
                    range: `${e.selections[0].start.line + 1}-${e.selections[0].end.line + 1}`
                });
            }
        });
    }

    private async _handleUserMessage(text: string, selectedCode?: { file: string; code: string; range: string }) {
        if (!this._view) return;

        // Send archetype info to webview
        this._view.webview.postMessage({
            command: 'archetypeInfo',
            name: this._projectArchetype,
            peak: this._archetypeData ? `${this._archetypeData.peakTokens.toLocaleString()} tokens` : 'Unknown',
            recommendation: this._getArchetypeRecommendation()
        });

        // Calculate token budget
        const promptTokens = this._estimatePromptTokens(text);
        const fileTokens = selectedCode ? this._getFileTokenCount(selectedCode.file) : 0;
        const totalContextTokens = promptTokens + fileTokens;

        // Check if context exceeds budget
        if (totalContextTokens > this.MAX_CONTEXT_TOKENS) {
            this._view.webview.postMessage({
                command: 'contextWarning',
                message: `Context budget exceeded! ${totalContextTokens.toLocaleString()} / ${this.MAX_CONTEXT_TOKENS.toLocaleString()} tokens. Please reduce input size.`,
                tokens: totalContextTokens,
                maxTokens: this.MAX_CONTEXT_TOKENS
            });
            return;
        }

        // Add user message
        this._messages.push({ role: 'user', content: text });

        // Build context-aware prompt
        let fullPrompt = text;

        if (selectedCode && selectedCode.code) {
            fullPrompt = `I'm looking at this code in ${selectedCode.file} (lines ${selectedCode.range}):

\`\`\`
${selectedCode.code}
\`\`\`

${text}`;
        }

        // Add workspace context for file structure questions
        if (text.toLowerCase().includes('file') || text.toLowerCase().includes('project') || text.toLowerCase().includes('structure')) {
            fullPrompt = `Workspace context:\n${this._workspaceContext}\n\n${fullPrompt}`;
        }

        try {
            this._view.webview.postMessage({ 
                command: 'showTyping',
                contextTokens: totalContextTokens,
                maxTokens: this.MAX_CONTEXT_TOKENS,
                fileTokens: fileTokens,
                promptTokens: promptTokens
            });

            // Call llama-server directly for chat
            const response = await fetch('http://127.0.0.1:8080/v1/chat/completions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    messages: [
                        {
                            role: 'system',
                            content: `You are APEX, an AI coding assistant with access to the user's entire workspace.

When asked about files, structure, or code:
- Reference specific files and their purposes
- Explain relationships between files
- Provide accurate code examples
- Be concise but thorough

Current workspace: ${this._workspaceContext.substring(0, 2000)}`
                        },
                        ...this._messages.slice(-15).map(m => ({
                            role: m.role,
                            content: m.content
                        }))
                    ],
                    max_tokens: 2048,
                    temperature: 0.7,
                    stream: false
                })
            });

            this._view.webview.postMessage({ command: 'hideTyping' });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json() as { choices?: Array<{ message?: { content?: string } }> };
            const assistantMessage = data.choices?.[0]?.message?.content || 'No response';

            this._messages.push({ role: 'assistant', content: assistantMessage });

            this._view.webview.postMessage({
                command: 'addMessage',
                role: 'assistant',
                content: assistantMessage,
                contextTokens: totalContextTokens,
                maxTokens: this.MAX_CONTEXT_TOKENS
            });

        } catch (error) {
            this._view.webview.postMessage({ command: 'hideTyping' });
            this._view.webview.postMessage({
                command: 'error',
                message: error instanceof Error ? error.message : 'Unknown error'
            });
        }
    }

    private async _buildWorkspaceContext() {
        const workspaceFolders = vscode.workspace.workspaceFolders;
        if (!workspaceFolders) {
            this._workspaceContext = 'No workspace folder opened';
            return;
        }

        let structure = 'Workspace Structure:\n';
        
        for (const folder of workspaceFolders) {
            structure += `\n📁 ${folder.name}/\n`;
            const files = await this._scanDirectory(folder.uri.fsPath, 3);
            structure += files;
        }

        this._workspaceContext = structure;
    }

    private async _loadTokenManifest() {
        try {
            const workspaceFolders = vscode.workspace.workspaceFolders;
            if (!workspaceFolders) return;

            const manifestPath = vscode.Uri.joinPath(
                workspaceFolders[0].uri,
                'token_manifest.json'
            );

            const manifestData = await vscode.workspace.fs.readFile(manifestPath);
            this._tokenManifest = JSON.parse(Buffer.from(manifestData).toString('utf-8'));
            
            console.log(`[APEX] Loaded token manifest: ${this._tokenManifest.total_files} files, ${this._tokenManifest.total_tokens.toLocaleString()} total tokens`);
        } catch (error) {
            console.error('[APEX] Failed to load token manifest:', error);
            this._tokenManifest = null;
        }
    }

    private _getFileTokenCount(filePath: string): number {
        if (!this._tokenManifest || !this._tokenManifest.files) {
            return 0;
        }

        const fileEntry = this._tokenManifest.files.find((f: any) => 
            f.path === filePath || f.path.endsWith(filePath)
        );

        return fileEntry ? fileEntry.tokens : 0;
    }

    private _estimatePromptTokens(text: string): number {
        // Rough estimate: 4 chars per token
        return Math.ceil(text.length / 4);
    }

    private _getArchetypeRecommendation(): string {
        if (!this._archetypeData) return 'Loading...';
        
        const peak = this._archetypeData.peakTokens;
        if (peak <= 10000) return '[OK] Safe for all GPUs';
        if (peak <= 20000) return '[OK] Safe for most GPUs';
        if (peak <= 35000) return '[WARN] Needs 24-32GB VRAM';
        if (peak <= 70000) return '[WARN] Needs 40GB+ VRAM';
        return '[FAIL] Use chunking/RAG';
    }

    private async _detectArchetype() {
        try {
            const workspaceFolders = vscode.workspace.workspaceFolders;
            if (!workspaceFolders) return;

            const layerlimitsPath = vscode.Uri.joinPath(
                workspaceFolders[0].uri,
                'layerlimits.json'
            );

            const layerlimitsData = await vscode.workspace.fs.readFile(layerlimitsPath);
            this._archetypeData = JSON.parse(Buffer.from(layerlimitsData).toString('utf-8'));
            
            // Simple detection: check for APE-specific files
            const files = await vscode.workspace.findFiles('**/*', '**/node_modules/**');
            const fileNames = files.map(f => f.path.split('/').pop() || '');
            
            if (fileNames.includes('layerlimits.json') && fileNames.includes('token_manifest.json')) {
                this._projectArchetype = 'APE Itself (ID:10)';
            } else if (fileNames.includes('unity') || fileNames.includes('uproject')) {
                this._projectArchetype = 'Game Engine (ID:05)';
            } else if (fileNames.includes('requirements.txt') && fileNames.includes('main.py')) {
                this._projectArchetype = 'REST API (ID:03)';
            } else {
                this._projectArchetype = 'Frontend (ID:01)';
            }
            
            console.log(`[APEX] Detected archetype: ${this._projectArchetype}`);
        } catch (error) {
            console.error('[APEX] Failed to detect archetype:', error);
            this._projectArchetype = 'Unknown';
        }
    }

    private async _scanDirectory(dirPath: string, maxDepth: number, currentDepth: number = 0): Promise<string> {
        if (currentDepth > maxDepth) return '';

        let result = '';
        const indent = '  '.repeat(currentDepth + 1);

        try {
            const entries = await vscode.workspace.fs.readDirectory(vscode.Uri.file(dirPath));
            
            // Sort: directories first, then files
            entries.sort((a, b) => {
                if (a[1] === vscode.FileType.Directory && b[1] !== vscode.FileType.Directory) return -1;
                if (a[1] !== vscode.FileType.Directory && b[1] === vscode.FileType.Directory) return 1;
                return a[0].localeCompare(b[0]);
            });

            // Filter out common ignored directories
            const ignored = ['node_modules', '.git', '__pycache__', 'dist', 'build', '.vscode', 'target', 'venv', '.venv'];

            for (const [name, type] of entries) {
                if (ignored.includes(name)) continue;
                if (name.startsWith('.')) continue;

                if (type === vscode.FileType.Directory) {
                    result += `${indent}📁 ${name}/\n`;
                    const subDir = await this._scanDirectory(
                        vscode.Uri.joinPath(vscode.Uri.file(dirPath), name).fsPath,
                        maxDepth,
                        currentDepth + 1
                    );
                    result += subDir;
                } else if (type === vscode.FileType.File) {
                    const ext = name.split('.').pop() || '';
                    const icon = this._getFileIcon(ext);
                    result += `${indent}${icon} ${name}\n`;
                }
            }
        } catch (error) {
            // Ignore errors for inaccessible directories
        }

        return result;
    }

    private _getFileIcon(ext: string): string {
        const icons: { [key: string]: string } = {
            'py': '🐍', 'js': '📜', 'ts': '📘', 'jsx': '⚛️', 'tsx': '⚛️',
            'html': '🌐', 'css': '🎨', 'scss': '🎨', 'less': '🎨',
            'json': '📋', 'yaml': '⚙️', 'yml': '⚙️', 'toml': '⚙️',
            'md': '📝', 'txt': '📄', 'rs': '🦀', 'go': '🔷',
            'java': '☕', 'cpp': '⚡', 'c': '⚡', 'h': '⚡', 'hpp': '⚡',
            'sh': '💻', 'bat': '💻', 'ps1': '💻', 'sql': '🗄️',
            'dockerfile': '🐳', 'gitignore': '🙈', 'env': '🔒'
        };
        return icons[ext.toLowerCase()] || '📄';
    }

    private _getHtmlForWebview(webview: vscode.Webview) {
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>APEX Chat</title>
    <style>
        :root {
            --container-padding: 12px;
            --input-padding: 8px;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: var(--vscode-font-family);
            font-size: var(--vscode-font-size);
            color: var(--vscode-foreground);
            background-color: var(--vscode-sideBar-background);
            height: 100vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        .header {
            padding: 10px var(--container-padding);
            border-bottom: 1px solid var(--vscode-widget-border);
            background: var(--vscode-sideBarSectionHeader-background);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .header h3 {
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--vscode-sideBarSectionHeader-foreground);
        }

        .header-actions {
            display: flex;
            gap: 4px;
        }

        .header-actions button {
            padding: 4px 8px;
            font-size: 11px;
            background: var(--vscode-button-secondaryBackground);
            color: var(--vscode-button-secondaryForeground);
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }

        .header-actions button:hover {
            background: var(--vscode-button-secondaryHoverBackground);
        }

        .token-budget {
            padding: 6px var(--container-padding);
            background: var(--vscode-editor-inactiveSelectionBackground);
            border-bottom: 1px solid var(--vscode-widget-border);
            font-size: 10px;
        }

        .token-budget-bar {
            height: 4px;
            background: var(--vscode-input-border);
            border-radius: 2px;
            overflow: hidden;
            margin-top: 4px;
        }

        .token-budget-fill {
            height: 100%;
            background: var(--vscode-terminal-ansiGreen);
            transition: width 0.3s, background-color 0.3s;
        }

        .token-budget-fill.warning {
            background: var(--vscode-terminal-ansiYellow);
        }

        .token-budget-fill.danger {
            background: var(--vscode-terminal-ansiRed);
        }

        .token-stats {
            display: flex;
            justify-content: space-between;
            margin-top: 4px;
            font-size: 9px;
            color: var(--vscode-descriptionForeground);
        }
        
        .chat-container {
            flex: 1;
            overflow-y: auto;
            padding: var(--container-padding);
        }
        
        .message {
            margin-bottom: 12px;
            display: flex;
            flex-direction: column;
        }
        
        .message.user {
            align-items: flex-end;
        }
        
        .message.assistant {
            align-items: flex-start;
        }
        
        .message-content {
            max-width: 90%;
            padding: 8px 12px;
            border-radius: 8px;
            line-height: 1.4;
            font-size: 12px;
        }
        
        .message.user .message-content {
            background-color: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border-bottom-right-radius: 2px;
        }
        
        .message.assistant .message-content {
            background-color: var(--vscode-editor-inactiveSelectionBackground);
            border-bottom-left-radius: 2px;
        }
        
        .message-content pre {
            background: var(--vscode-textCodeBlock-background);
            padding: 8px;
            border-radius: 4px;
            overflow-x: auto;
            margin: 6px 0;
            font-size: 11px;
        }
        
        .message-content code {
            font-family: var(--vscode-editor-font-family);
            font-size: var(--vscode-editor-font-size);
        }
        
        .message-content p {
            margin-bottom: 6px;
        }
        
        .message-content p:last-child {
            margin-bottom: 0;
        }
        
        .input-container {
            border-top: 1px solid var(--vscode-widget-border);
            padding: var(--container-padding);
            background: var(--vscode-sideBar-background);
        }
        
        .selection-info {
            font-size: 10px;
            color: var(--vscode-descriptionForeground);
            padding: 4px 0;
            display: none;
        }
        
        .selection-info.visible {
            display: block;
        }
        
        .selection-info code {
            background: var(--vscode-textCodeBlock-background);
            padding: 2px 4px;
            border-radius: 3px;
        }
        
        textarea {
            width: 100%;
            resize: none;
            min-height: 60px;
            max-height: 120px;
            padding: var(--input-padding);
            border-radius: 6px;
            border: 1px solid var(--vscode-input-border);
            background: var(--vscode-input-background);
            color: var(--vscode-input-foreground);
            font-family: var(--vscode-font-family);
            font-size: 12px;
        }
        
        textarea:focus {
            outline: 1px solid var(--vscode-focusBorder);
        }
        
        .send-btn {
            width: 100%;
            margin-top: 6px;
            padding: 8px;
            background: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 600;
            font-size: 12px;
        }
        
        .send-btn:hover {
            background: var(--vscode-button-hoverBackground);
        }
        
        .send-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .typing-indicator {
            display: flex;
            gap: 3px;
            padding: 8px 12px;
        }
        
        .typing-indicator span {
            width: 6px;
            height: 6px;
            background: var(--vscode-descriptionForeground);
            border-radius: 50%;
            animation: bounce 1.4s infinite ease-in-out;
        }
        
        .typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
        .typing-indicator span:nth-child(2) { animation-delay: -0.16s; }
        
        @keyframes bounce {
            0%, 80%, 100% { transform: scale(0); }
            40% { transform: scale(1); }
        }
        
        .welcome {
            text-align: center;
            padding: 20px 10px;
            color: var(--vscode-descriptionForeground);
        }
        
        .welcome h4 {
            color: var(--vscode-foreground);
            margin-bottom: 8px;
        }
        
        .welcome-tips {
            font-size: 11px;
            text-align: left;
            margin-top: 12px;
            padding: 8px;
            background: var(--vscode-editor-inactiveSelectionBackground);
            border-radius: 6px;
        }
        
        .welcome-tips li {
            margin-bottom: 4px;
        }
        
        .workspace-preview {
            font-size: 10px;
            color: var(--vscode-descriptionForeground);
            padding: 8px;
            background: var(--vscode-textCodeBlock-background);
            border-radius: 4px;
            margin-top: 8px;
            max-height: 100px;
            overflow-y: auto;
            font-family: var(--vscode-editor-font-family);
            white-space: pre-wrap;
        }
    </style>
</head>
<body>
    <div class="header">
        <h3>🤖 APEX Chat</h3>
        <div class="header-actions">
            <button onclick="clearChat()">Clear</button>
            <button onclick="showWorkspace()">Workspace</button>
        </div>
    </div>

    <div class="token-budget" id="tokenBudget" style="display:none;">
        <div id="tokenBudgetText">Context: 0 / 32,768 tokens</div>
        <div class="token-budget-bar">
            <div class="token-budget-fill" id="tokenBudgetFill" style="width: 0%"></div>
        </div>
        <div class="token-stats">
            <span id="promptTokens">Prompt: 0</span>
            <span id="fileTokens">File: 0</span>
        </div>
    </div>

    <div class="archetype-info" id="archetypeInfo" style="display:none; padding: 8px 12px; font-size: 10px; background: var(--vscode-editor-inactiveSelectionBackground); border-bottom: 1px solid var(--vscode-widget-border);">
        <strong>Project:</strong> <span id="archetypeName">Unknown</span> | 
        <strong>Peak:</strong> <span id="archetypePeak">-</span> | 
        <strong>Recommendation:</strong> <span id="archetypeRec">-</span>
    </div>

    <div class="chat-container" id="chatContainer">
        <div class="welcome" id="welcomeMsg">
            <h4>AI Code Assistant</h4>
            <p>Ask about your codebase!</p>
            <ul class="welcome-tips">
                <li>📁 "What files are in this project?"</li>
                <li>🔍 "Explain the selected code"</li>
                <li>🐛 "Find bugs in this function"</li>
                <li>✨ "How do I improve this?"</li>
            </ul>
        </div>
    </div>
    
    <div class="input-container">
        <div class="selection-info" id="selectionInfo"></div>
        <textarea
            id="messageInput"
            placeholder="Ask about your code..."
            rows="3"
        ></textarea>
        <button class="send-btn" id="sendBtn">Send</button>
    </div>

    <script>
        (function() {
            const vscode = acquireVsCodeApi();
            let isLoading = false;
            let currentSelection = null;
            const MAX_TOKENS = 32768;

            // Get elements
            const messageInput = document.getElementById('messageInput');
            const sendBtn = document.getElementById('sendBtn');
            const selectionInfo = document.getElementById('selectionInfo');
            const chatContainer = document.getElementById('chatContainer');
            const welcomeMsg = document.getElementById('welcomeMsg');
            const tokenBudget = document.getElementById('tokenBudget');
            const tokenBudgetText = document.getElementById('tokenBudgetText');
            const tokenBudgetFill = document.getElementById('tokenBudgetFill');
            const promptTokensEl = document.getElementById('promptTokens');
            const fileTokensEl = document.getElementById('fileTokens');
            const archetypeInfo = document.getElementById('archetypeInfo');
            const archetypeName = document.getElementById('archetypeName');
            const archetypePeak = document.getElementById('archetypePeak');
            const archetypeRec = document.getElementById('archetypeRec');

            // Show archetype info
            function showArchetype(name, peak, rec) {
                if (!archetypeInfo) return;
                archetypeInfo.style.display = 'block';
                archetypeName.textContent = name;
                archetypePeak.textContent = peak;
                archetypeRec.textContent = rec;
            }

            // Update token budget display
            function updateTokenBudget(contextTokens, maxTokens, fileTokens, promptTokens) {
                if (!tokenBudget) return;

                tokenBudget.style.display = 'block';
                const percentage = Math.min(100, (contextTokens / maxTokens) * 100);

                tokenBudgetText.textContent = 'Context: ' + contextTokens.toLocaleString() + ' / ' + maxTokens.toLocaleString() + ' tokens';
                tokenBudgetFill.style.width = percentage + '%';

                // Update color based on usage
                tokenBudgetFill.classList.remove('warning', 'danger');
                if (percentage > 90) {
                    tokenBudgetFill.classList.add('danger');
                } else if (percentage > 70) {
                    tokenBudgetFill.classList.add('warning');
                }

                if (promptTokensEl) promptTokensEl.textContent = 'Prompt: ' + (promptTokens ? promptTokens.toLocaleString() : 0);
                if (fileTokensEl) fileTokensEl.textContent = 'File: ' + (fileTokens ? fileTokens.toLocaleString() : 0);
            }

            // Send message function
            function sendMessage() {
                if (!messageInput) return;
                const text = messageInput.value.trim();
                if (!text || isLoading) return;

                messageInput.value = '';
                isLoading = true;
                if (sendBtn) sendBtn.disabled = true;

                vscode.postMessage({
                    command: 'sendMessage',
                    text: text,
                    selectedCode: currentSelection
                });
            }

            // Add event listeners
            if (sendBtn) {
                sendBtn.addEventListener('click', sendMessage);
            }

            if (messageInput) {
                messageInput.addEventListener('keydown', function(event) {
                    if (event.key === 'Enter' && !event.shiftKey) {
                        event.preventDefault();
                        sendMessage();
                    }
                });
            }

            // Listen for messages from extension
            window.addEventListener('message', function(event) {
                const message = event.data;
                switch (message.command) {
                    case 'addMessage':
                        if (welcomeMsg) welcomeMsg.style.display = 'none';
                        addMessage(message.role, message.content);
                        isLoading = false;
                        if (sendBtn) sendBtn.disabled = false;
                        if (messageInput) messageInput.focus();
                        // Update token budget if provided
                        if (message.contextTokens && message.maxTokens) {
                            updateTokenBudget(message.contextTokens, message.maxTokens, message.fileTokens || 0, message.promptTokens || 0);
                        }
                        break;
                    case 'showTyping':
                        showTyping();
                        // Update token budget if provided
                        if (message.contextTokens && message.maxTokens) {
                            updateTokenBudget(message.contextTokens, message.maxTokens, message.fileTokens || 0, message.promptTokens || 0);
                        }
                        break;
                    case 'hideTyping':
                        hideTyping();
                        isLoading = false;
                        if (sendBtn) sendBtn.disabled = false;
                        break;
                    case 'contextWarning':
                        if (welcomeMsg) welcomeMsg.style.display = 'none';
                        addMessage('assistant', 'Context Budget Exceeded: ' + message.message);
                        isLoading = false;
                        if (sendBtn) sendBtn.disabled = false;
                        updateTokenBudget(message.tokens, message.maxTokens, 0, message.tokens);
                        break;
                    case 'clearChat':
                        if (chatContainer) chatContainer.innerHTML = '';
                        if (welcomeMsg) welcomeMsg.style.display = 'block';
                        break;
                    case 'selectionChanged':
                        currentSelection = message;
                        if (selectionInfo && message) {
                            var fileName = message.file.split('/').pop();
                            selectionInfo.innerHTML = 'Selected: <code>' + fileName + ':' + message.range + '</code>';
                            selectionInfo.classList.add('visible');
                        }
                        break;
                    case 'workspaceInfo':
                        if (welcomeMsg) welcomeMsg.style.display = 'none';
                        var bt = String.fromCharCode(96);
                        addMessage('assistant', 'Workspace Structure:\\n\\n' + bt + bt + bt + '\\n' + message.workspace + '\\n' + bt + bt + bt);
                        break;
                    case 'error':
                        if (welcomeMsg) welcomeMsg.style.display = 'none';
                        addMessage('assistant', 'Error: ' + message.message);
                        isLoading = false;
                        if (sendBtn) sendBtn.disabled = false;
                        break;
                    case 'archetypeInfo':
                        showArchetype(message.name, message.peak, message.recommendation);
                        break;
                }
            });

            // Add message to chat
            function addMessage(role, content) {
                if (!chatContainer) return;
                const messageDiv = document.createElement('div');
                messageDiv.className = 'message ' + role;

                // Format content
                var bt = String.fromCharCode(96);
                var formatted = content.split('\\n').join('<br>');
                formatted = formatted.replace(new RegExp(bt + bt + bt, 'g'), '<pre><code>');
                formatted = formatted.replace(new RegExp(bt, 'g'), '<code>');

                messageDiv.innerHTML = '<div class="message-content">' + formatted + '</div>';
                chatContainer.appendChild(messageDiv);
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }

            // Show typing indicator
            function showTyping() {
                if (!chatContainer) return;
                const typing = document.createElement('div');
                typing.className = 'message assistant';
                typing.id = 'typingIndicator';
                typing.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';
                chatContainer.appendChild(typing);
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }

            // Hide typing indicator
            function hideTyping() {
                const typing = document.getElementById('typingIndicator');
                if (typing) typing.remove();
            }
        })();
    </script>
</body>
</html>`;
    }

    public refreshWorkspace() {
        this._buildWorkspaceContext();
    }
}
