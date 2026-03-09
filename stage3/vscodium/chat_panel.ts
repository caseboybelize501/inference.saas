// APEX Chat Sidebar - Interactive AI Chat for Code

import * as vscode from 'vscode';
import { IntelligenceClient } from './intelligence_client';

export class ChatPanel {
    public static currentPanel: ChatPanel | undefined;
    public static readonly viewType = 'apex.chat';

    private readonly _panel: vscode.WebviewPanel;
    private readonly _intelligenceClient: IntelligenceClient;
    private _disposables: vscode.Disposable[] = [];
    private _messages: Array<{ role: 'user' | 'assistant'; content: string }> = [];

    public static createOrShow(client: IntelligenceClient) {
        const column = vscode.window.activeTextEditor
            ? vscode.window.activeTextEditor.viewColumn
            : undefined;

        // If panel already exists, show it
        if (ChatPanel.currentPanel) {
            ChatPanel.currentPanel._panel.reveal(column);
            return;
        }

        // Create new panel
        const panel = vscode.window.createWebviewPanel(
            ChatPanel.viewType,
            'APEX AI Chat',
            column || vscode.ViewColumn.Two,
            {
                enableScripts: true,
                localResourceRoots: [],
                retainContextWhenHidden: true
            }
        );

        ChatPanel.currentPanel = new ChatPanel(panel, client);
    }

    private constructor(panel: vscode.WebviewPanel, client: IntelligenceClient) {
        this._panel = panel;
        this._intelligenceClient = client;

        // Set HTML content
        this._updateWebviewContent();

        // Handle messages from webview
        this._panel.webview.onDidReceiveMessage(
            async (message) => {
                switch (message.command) {
                    case 'sendMessage':
                        await this._handleUserMessage(message.text);
                        break;
                    case 'clearChat':
                        this._messages = [];
                        this._panel.webview.postMessage({ command: 'clearChat' });
                        break;
                }
            },
            null,
            this._disposables
        );

        // Handle panel close
        this._panel.onDidDispose(
            () => {
                ChatPanel.currentPanel = undefined;
                this._disposables.forEach((d) => d.dispose());
            },
            null,
            this._disposables
        );
    }

    private async _handleUserMessage(text: string) {
        // Add user message to history
        this._messages.push({ role: 'user', content: text });

        // Get selected code if any
        const editor = vscode.window.activeTextEditor;
        let selectedCode: string | undefined;
        let fileInfo: string | undefined;

        if (editor && !editor.selection.isEmpty) {
            selectedCode = editor.document.getText(editor.selection);
            fileInfo = `${editor.document.fileName}:${editor.selection.start.line + 1}-${editor.selection.end.line + 1}`;
        }

        // Build prompt with context
        let fullPrompt = text;
        if (selectedCode) {
            fullPrompt = `Context from ${fileInfo}:\n\`\`\`\n${selectedCode}\n\`\`\`\n\nQuestion: ${text}`;
        }

        // Send to intelligence API
        try {
            // Show typing indicator
            this._panel.webview.postMessage({ command: 'showTyping' });

            // Call the completion endpoint
            const response = await this._intelligenceClient.complete(
                editor?.document.uri.fsPath || '',
                editor?.selection.active.line || 0,
                0,
                fullPrompt,
                '',
                512
            );

            // Remove typing indicator
            this._panel.webview.postMessage({ command: 'hideTyping' });

            if (response && response.completion) {
                const assistantMessage = response.completion;
                this._messages.push({ role: 'assistant', content: assistantMessage });

                // Add to chat
                this._panel.webview.postMessage({
                    command: 'addMessage',
                    role: 'assistant',
                    content: assistantMessage
                });
            } else {
                // Fallback: use llama-server directly
                const directResponse = await this._callLlamaServer(fullPrompt);
                this._messages.push({ role: 'assistant', content: directResponse });
                this._panel.webview.postMessage({
                    command: 'addMessage',
                    role: 'assistant',
                    content: directResponse
                });
            }
        } catch (error) {
            this._panel.webview.postMessage({ command: 'hideTyping' });
            this._panel.webview.postMessage({
                command: 'addError',
                content: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`
            });
        }
    }

    private async _callLlamaServer(prompt: string): Promise<string> {
        // Direct call to llama-server on port 8080
        const response = await fetch('http://127.0.0.1:8080/v1/chat/completions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                messages: [
                    {
                        role: 'system',
                        content: 'You are APEX, an AI coding assistant. Provide clear, concise, and helpful code explanations and solutions.'
                    },
                    ...this._messages.slice(-10).map(m => ({
                        role: m.role,
                        content: m.content
                    }))
                ],
                max_tokens: 512,
                temperature: 0.7
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json() as { choices?: Array<{ message?: { content?: string } }> };
        return data.choices?.[0]?.message?.content || 'No response generated';
    }

    private _updateWebviewContent() {
        this._panel.title = 'APEX AI Chat';
        this._panel.webview.html = this._getHtmlForWebview();
    }

    private _getHtmlForWebview() {
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>APEX Chat</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: var(--vscode-font-family);
            font-size: var(--vscode-font-size);
            color: var(--vscode-foreground);
            background-color: var(--vscode-editor-background);
            height: 100vh;
            display: flex;
            flex-direction: column;
        }
        
        .chat-container {
            flex: 1;
            overflow-y: auto;
            padding: 16px;
        }
        
        .message {
            margin-bottom: 16px;
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
            max-width: 85%;
            padding: 10px 14px;
            border-radius: 12px;
            line-height: 1.5;
        }
        
        .message.user .message-content {
            background-color: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border-bottom-right-radius: 4px;
        }
        
        .message.assistant .message-content {
            background-color: var(--vscode-editor-inactiveSelectionBackground);
            border-bottom-left-radius: 4px;
        }
        
        .message-content pre {
            background-color: var(--vscode-textCodeBlock-background);
            padding: 12px;
            border-radius: 6px;
            overflow-x: auto;
            margin: 8px 0;
        }
        
        .message-content code {
            font-family: var(--vscode-editor-font-family);
            font-size: var(--vscode-editor-font-size);
        }
        
        .input-container {
            border-top: 1px solid var(--vscode-widget-border);
            padding: 16px;
            background-color: var(--vscode-editor-background);
        }
        
        .input-wrapper {
            display: flex;
            gap: 8px;
            align-items: flex-end;
        }
        
        textarea {
            flex: 1;
            resize: none;
            min-height: 50px;
            max-height: 150px;
            padding: 10px 14px;
            border-radius: 8px;
            border: 1px solid var(--vscode-input-border);
            background-color: var(--vscode-input-background);
            color: var(--vscode-input-foreground);
            font-family: var(--vscode-font-family);
            font-size: var(--vscode-font-size);
        }
        
        textarea:focus {
            outline: 1px solid var(--vscode-focusBorder);
        }
        
        button {
            padding: 10px 20px;
            border-radius: 8px;
            border: none;
            background-color: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            cursor: pointer;
            font-weight: 600;
            transition: background-color 0.2s;
        }
        
        button:hover {
            background-color: var(--vscode-button-hoverBackground);
        }
        
        button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .typing-indicator {
            display: flex;
            gap: 4px;
            padding: 10px 14px;
            align-items: center;
        }
        
        .typing-indicator span {
            width: 8px;
            height: 8px;
            background-color: var(--vscode-descriptionForeground);
            border-radius: 50%;
            animation: bounce 1.4s infinite ease-in-out;
        }
        
        .typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
        .typing-indicator span:nth-child(2) { animation-delay: -0.16s; }
        
        @keyframes bounce {
            0%, 80%, 100% { transform: scale(0); }
            40% { transform: scale(1); }
        }
        
        .welcome-message {
            text-align: center;
            padding: 40px 20px;
            color: var(--vscode-descriptionForeground);
        }
        
        .welcome-message h2 {
            margin-bottom: 12px;
            color: var(--vscode-foreground);
        }
        
        .quick-actions {
            display: flex;
            gap: 8px;
            justify-content: center;
            margin-top: 16px;
            flex-wrap: wrap;
        }
        
        .quick-action-btn {
            padding: 6px 12px;
            font-size: 12px;
            background-color: var(--vscode-button-secondaryBackground);
        }
        
        .quick-action-btn:hover {
            background-color: var(--vscode-button-secondaryHoverBackground);
        }
    </style>
</head>
<body>
    <div class="chat-container" id="chatContainer">
        <div class="welcome-message">
            <h2>🤖 APEX AI Chat</h2>
            <p>Your AI coding assistant is ready to help!</p>
            <div class="quick-actions">
                <button class="quick-action-btn" onclick="sendQuickAction('Explain this code')">📖 Explain Code</button>
                <button class="quick-action-btn" onclick="sendQuickAction('Find bugs in this code')">🐛 Find Bugs</button>
                <button class="quick-action-btn" onclick="sendQuickAction('Suggest improvements')">✨ Improve Code</button>
                <button class="quick-action-btn" onclick="sendQuickAction('Add comments to this code')">📝 Add Comments</button>
            </div>
        </div>
    </div>
    
    <div class="input-container">
        <div class="input-wrapper">
            <textarea 
                id="messageInput" 
                placeholder="Ask about your code..." 
                rows="2"
                onkeydown="handleKeyDown(event)"
            ></textarea>
            <button id="sendBtn" onclick="sendMessage()">Send</button>
        </div>
    </div>
    
    <script>
        const vscode = acquireVsCodeApi();
        const chatContainer = document.getElementById('chatContainer');
        const messageInput = document.getElementById('messageInput');
        const sendBtn = document.getElementById('sendBtn');
        
        let isLoading = false;
        
        function handleKeyDown(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendMessage();
            }
        }
        
        function sendMessage() {
            const text = messageInput.value.trim();
            if (!text || isLoading) return;
            
            messageInput.value = '';
            isLoading = true;
            sendBtn.disabled = true;
            
            vscode.postMessage({ command: 'sendMessage', text });
        }
        
        function sendQuickAction(text) {
            vscode.postMessage({ command: 'sendMessage', text });
        }
        
        function addMessage(role, content) {
            // Remove welcome message if it exists
            const welcome = chatContainer.querySelector('.welcome-message');
            if (welcome) welcome.remove();
            
            const messageDiv = document.createElement('div');
            messageDiv.className = \`message \${role}\`;
            
            // Simple markdown-like code block formatting
            const formattedContent = content
                .replace(/\`\`\`(\w*)\n?([\s\S]*?)\`\`\`/g, '<pre><code class="language-$1">$2</code></pre>')
                .replace(/\`([^\`]+)\`/g, '<code>$1</code>')
                .replace(/\n/g, '<br>');
            
            messageDiv.innerHTML = \`
                <div class="message-content">\${formattedContent}</div>
            \`;
            
            chatContainer.appendChild(messageDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
        
        function showTyping() {
            const typingDiv = document.createElement('div');
            typingDiv.className = 'message assistant';
            typingDiv.id = 'typingIndicator';
            typingDiv.innerHTML = \`
                <div class="typing-indicator">
                    <span></span><span></span><span></span>
                </div>
            \`;
            chatContainer.appendChild(typingDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
        
        function hideTyping() {
            const typing = document.getElementById('typingIndicator');
            if (typing) typing.remove();
        }
        
        function clearChat() {
            chatContainer.innerHTML = '';
            location.reload();
        }
        
        window.addEventListener('message', event => {
            const message = event.data;
            switch (message.command) {
                case 'addMessage':
                    addMessage(message.role, message.content);
                    isLoading = false;
                    sendBtn.disabled = false;
                    messageInput.focus();
                    break;
                case 'showTyping':
                    showTyping();
                    break;
                case 'hideTyping':
                    hideTyping();
                    isLoading = false;
                    sendBtn.disabled = false;
                    break;
                case 'clearChat':
                    clearChat();
                    break;
            }
        });
        
        // Focus input on load
        messageInput.focus();
    </script>
</body>
</html>`;
    }
}
