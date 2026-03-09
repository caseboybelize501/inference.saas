// VSCodium Extension - APEX AI Code Intelligence

import * as vscode from 'vscode';
import { IntelligenceClient } from './intelligence_client';
import { CompletionProvider } from './completion';
import { HoverProvider } from './hover';
import { StatusBar } from './status_bar';
import { SidebarChatProvider } from './sidebar_chat';

let intelligenceClient: IntelligenceClient | undefined;
let completionProvider: CompletionProvider | undefined;
let hoverProviderInstance: HoverProvider | undefined;
let statusBar: StatusBar | undefined;
let statusPollTimer: NodeJS.Timeout | undefined;
let sidebarChatProvider: SidebarChatProvider | undefined;

const INTELLIGENCE_API_URL = 'http://localhost:3001';

export function activate(context: vscode.ExtensionContext) {
    console.log('APEX: Activating extension...');

    // Initialize intelligence client
    intelligenceClient = new IntelligenceClient(INTELLIGENCE_API_URL);

    // Initialize status bar
    statusBar = new StatusBar();
    statusBar.updateConnecting();

    // Initialize sidebar chat provider - ALWAYS register for RIGHT activity bar
    if (intelligenceClient) {
        sidebarChatProvider = new SidebarChatProvider(context.extensionUri, intelligenceClient);
        const sidebarDisposable = vscode.window.registerWebviewViewProvider(
            SidebarChatProvider.viewType,
            sidebarChatProvider,
            {
                webviewOptions: {
                    retainContextWhenHidden: true
                }
            }
        );
        context.subscriptions.push(sidebarDisposable);
        
        // Auto-open chat panel on startup if enabled
        const config = vscode.workspace.getConfiguration('apex');
        if (config.get('autoOpenChat', true)) {
            setTimeout(() => {
                // Open the chat panel in the right activity bar
                vscode.commands.executeCommand('apex-activitybar.focus');
                vscode.commands.executeCommand('apex.chatSidebar.focus');
            }, 1000);
        }
    }

    // Initialize completion provider
    completionProvider = new CompletionProvider(intelligenceClient, statusBar);
    const completionDisposable = vscode.languages.registerInlineCompletionItemProvider(
        { pattern: '**/*' },
        completionProvider
    );
    context.subscriptions.push(completionDisposable);

    // Initialize hover provider
    hoverProviderInstance = new HoverProvider(intelligenceClient, statusBar);
    const hoverDisposable = vscode.languages.registerHoverProvider(
        { pattern: '**/*' },
        hoverProviderInstance
    );
    context.subscriptions.push(hoverDisposable);

    // Register commands
    const completeCommand = vscode.commands.registerCommand('apex.complete', async () => {
        if (completionProvider) {
            await completionProvider.triggerManualCompletion();
        }
    });
    context.subscriptions.push(completeCommand);

    const explainCommand = vscode.commands.registerCommand('apex.explain', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor || !hoverProviderInstance) return;

        const selection = editor.selection;
        if (selection.isEmpty) {
            vscode.window.showWarningMessage('Please select code to explain');
            return;
        }

        await hoverProviderInstance.explainSelection(editor, selection);
    });
    context.subscriptions.push(explainCommand);

    const refactorCommand = vscode.commands.registerCommand('apex.refactor', async () => {
        const editor = vscode.window.activeTextEditor;
        if (!editor) return;

        const selection = editor.selection;
        if (selection.isEmpty) {
            vscode.window.showWarningMessage('Please select code to refactor');
            return;
        }

        const instruction = await vscode.window.showInputBox({
            prompt: 'Refactoring instruction',
            placeHolder: 'e.g., Extract method, Simplify logic, Add error handling...'
        });

        if (instruction && intelligenceClient) {
            await intelligenceClient.refactor(
                editor.document.uri.fsPath,
                selection.start.line,
                selection.end.line,
                instruction
            );
        }
    });
    context.subscriptions.push(refactorCommand);

    // Chat command - opens sidebar
    const chatCommand = vscode.commands.registerCommand('apex.chat', async () => {
        await vscode.commands.executeCommand('apex.chatSidebar.focus');
    });
    context.subscriptions.push(chatCommand);

    // Focus command - opens APEX chat on right side
    const focusCommand = vscode.commands.registerCommand('apex.focus', async () => {
        vscode.commands.executeCommand('workbench.action.openAuxiliaryBar');
        vscode.commands.executeCommand('apex.chatSidebar.focus');
    });
    context.subscriptions.push(focusCommand);

    // Show status command
    const showStatusCommand = vscode.commands.registerCommand('apex.showStatus', async () => {
        const health = await intelligenceClient?.healthCheck();
        vscode.window.showInformationMessage(
            `APEX Status: ${health ? '✅ Connected' : '❌ Disconnected'}\n` +
            `Server: ${INTELLIGENCE_API_URL}\n` +
            `Services: Stage 1 (3000), Stage 2 (3001), llama.cpp (8080)`
        );
    });
    context.subscriptions.push(showStatusCommand);

    // Rebuild index command
    const rebuildIndexCommand = vscode.commands.registerCommand('apex.rebuildIndex', async () => {
        vscode.window.showInformationMessage('Index rebuild initiated. This may take a few minutes...');
        try {
            await vscode.commands.executeCommand('workbench.action.openTerminal');
        } catch (error) {
            vscode.window.showErrorMessage('Failed to rebuild index: ' + error);
        }
    });
    context.subscriptions.push(rebuildIndexCommand);

    // Start polling status
    startStatusPolling();

    // Update status bar
    if (statusBar) {
        statusBar.updateConnected();
    }

    console.log('APEX: Extension activated');
}

function startStatusPolling() {
    // Poll index status every 30 seconds
    statusPollTimer = setInterval(async () => {
        if (intelligenceClient && statusBar) {
            try {
                const status = await intelligenceClient.getIndexStatus();
                statusBar.updateIndexStatus(status);
            } catch (error) {
                statusBar.updateError();
            }
        }
    }, 30000);
}

export function deactivate() {
    console.log('APEX: Deactivating extension...');

    if (statusPollTimer) {
        clearInterval(statusPollTimer);
    }

    if (intelligenceClient) {
        intelligenceClient.dispose();
    }

    if (statusBar) {
        statusBar.dispose();
    }
}
