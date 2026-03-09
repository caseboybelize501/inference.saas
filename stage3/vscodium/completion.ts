// Completion Provider - On-demand code completion

import * as vscode from 'vscode';
import { IntelligenceClient, CompletionResult } from './intelligence_client';
import { StatusBar } from './status_bar';

export class CompletionProvider implements vscode.InlineCompletionItemProvider {
    private client: IntelligenceClient;
    private statusBar: StatusBar;
    private pendingRequest: AbortController | null = null;
    private lastCompletion: CompletionResult | null = null;
    private lastCompletionRange: vscode.Range | null = null;

    constructor(client: IntelligenceClient, statusBar: StatusBar) {
        this.client = client;
        this.statusBar = statusBar;
    }

    async provideInlineCompletionItems(
        document: vscode.TextDocument,
        position: vscode.Position,
        context: vscode.InlineCompletionContext,
        token: vscode.CancellationToken
    ): Promise<vscode.InlineCompletionList | null> {
        // Only trigger on explicit invocation (Ctrl+Shift+A)
        if (context.triggerKind !== vscode.InlineCompletionTriggerKind.Invoke) {
            return null;
        }

        // Cancel any pending request
        if (this.pendingRequest) {
            this.pendingRequest.abort();
        }

        this.pendingRequest = new AbortController();

        try {
            this.statusBar.updateLoading();

            // Get prefix and suffix
            const prefix = document.getText(new vscode.Range(new vscode.Position(0, 0), position));
            const suffix = document.getText(new vscode.Range(position, document.positionAt(document.getText().length)));

            // Get last 10 lines as context for query
            const startLine = Math.max(0, position.line - 10);
            const query = document.getText(new vscode.Range(startLine, 0, position.line, position.character));

            // Request completion
            const result = await this.client.complete(
                document.uri.fsPath,
                position.line,
                position.character,
                prefix,
                suffix,
                256
            );

            if (!result || !result.completion) {
                this.statusBar.updateConnected();
                return null;
            }

            this.lastCompletion = result;
            this.statusBar.updateConnected();

            // Create inline completion item
            const completionItem = new vscode.InlineCompletionItem(
                result.completion,
                new vscode.Range(position, position)
            );

            completionItem.command = {
                command: 'apex.acceptCompletion',
                title: 'Accept completion'
            };

            return new vscode.InlineCompletionList([completionItem]);

        } catch (error) {
            if (error instanceof Error && error.name === 'AbortError') {
                return null; // Request was cancelled
            }

            console.error('APEX: Completion error:', error);
            this.statusBar.updateError();
            return null;

        } finally {
            this.pendingRequest = null;
        }
    }

    async triggerManualCompletion(): Promise<void> {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showWarningMessage('No active editor');
            return;
        }

        // Trigger inline completion
        await vscode.commands.executeCommand('editor.action.inlineSuggest.trigger');
    }

    acceptCompletion(): void {
        // Handle completion acceptance
        console.log('APEX: Completion accepted');
    }

    dispose() {
        if (this.pendingRequest) {
            this.pendingRequest.abort();
        }
    }
}
