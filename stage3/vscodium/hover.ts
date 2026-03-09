// Hover Provider - Symbol hover with explanations

import * as vscode from 'vscode';
import { IntelligenceClient, ExplainResult, Symbol } from './intelligence_client';
import { StatusBar } from './status_bar';

export class HoverProvider implements vscode.HoverProvider {
    private client: IntelligenceClient;
    private statusBar: StatusBar;

    constructor(client: IntelligenceClient, statusBar: StatusBar) {
        this.client = client;
        this.statusBar = statusBar;
    }

    async provideHover(
        document: vscode.TextDocument,
        position: vscode.Position,
        token: vscode.CancellationToken
    ): Promise<vscode.Hover | null> {
        // Get the word at position
        const range = document.getWordRangeAtPosition(position);
        if (!range) {
            return null;
        }

        const word = document.getText(range);
        
        // Skip common keywords and short words
        if (this.isSkipWord(word)) {
            return null;
        }

        try {
            this.statusBar.updateLoading();

            // Get symbols in file
            const symbols = await this.client.getSymbols(document.uri.fsPath);
            
            // Find symbol at position
            const symbolAtPosition = symbols.find(s => 
                s.line === position.line && 
                s.name === word
            );

            if (!symbolAtPosition) {
                this.statusBar.updateConnected();
                return null;
            }

            // Request explanation
            const result = await this.client.explain(
                document.uri.fsPath,
                symbolAtPosition.line,
                symbolAtPosition.line + 1,
                `Explain the purpose and usage of ${word}`
            );

            this.statusBar.updateConnected();

            if (!result) {
                // Fallback: show basic symbol info
                return this.createBasicHover(symbolAtPosition);
            }

            return this.createExplainHover(result, symbolAtPosition);

        } catch (error) {
            console.error('APEX: Hover error:', error);
            this.statusBar.updateError();
            return null;
        }
    }

    async explainSelection(
        editor: vscode.TextEditor,
        selection: vscode.Selection
    ): Promise<void> {
        try {
            this.statusBar.updateLoading();

            const selectedCode = editor.document.getText(selection);

            const result = await this.client.explain(
                editor.document.uri.fsPath,
                selection.start.line,
                selection.end.line,
                'Explain what this code does'
            );

            this.statusBar.updateConnected();

            if (!result || !result.explanation) {
                vscode.window.showWarningMessage('Could not get explanation');
                return;
            }

            // Show explanation in webview panel
            const panel = vscode.window.createWebviewPanel(
                'apexExplanation',
                'APEX Explanation',
                vscode.ViewColumn.Beside,
                {}
            );

            panel.webview.html = this.createExplanationHtml(
                result.explanation,
                result.symbols_referenced,
                selectedCode
            );

        } catch (error) {
            console.error('APEX: Explain error:', error);
            this.statusBar.updateError();
            vscode.window.showErrorMessage('Failed to get explanation');
        }
    }

    private isSkipWord(word: string): boolean {
        const skipWords = new Set([
            'the', 'a', 'an', 'is', 'are', 'was', 'were',
            'if', 'else', 'for', 'while', 'return', 'break',
            'import', 'from', 'export', 'default', 'class',
            'function', 'const', 'let', 'var', 'def',
            'public', 'private', 'protected', 'static'
        ]);
        return skipWords.has(word.toLowerCase()) || word.length < 2;
    }

    private createBasicHover(symbol: Symbol): vscode.Hover {
        const contents = new vscode.MarkdownString();
        contents.appendCodeblock(`${symbol.kind} ${symbol.name}`, 'typescript');
        
        if (symbol.docstring) {
            contents.appendMarkdown('\n\n---\n\n');
            contents.appendMarkdown(symbol.docstring);
        }

        return new vscode.Hover(contents);
    }

    private createExplainHover(result: ExplainResult, symbol: Symbol): vscode.Hover {
        const contents = new vscode.MarkdownString();
        contents.appendCodeblock(`${symbol.kind} ${symbol.name}`, 'typescript');
        
        contents.appendMarkdown('\n\n---\n\n');
        contents.appendMarkdown(result.explanation);

        if (result.symbols_referenced.length > 0) {
            contents.appendMarkdown('\n\n---\n\n');
            contents.appendMarkdown('**Related symbols:**\n\n');
            for (const ref of result.symbols_referenced.slice(0, 5)) {
                contents.appendMarkdown(`- \`${ref}\`\n`);
            }
        }

        return new vscode.Hover(contents);
    }

    private createExplanationHtml(
        explanation: string,
        symbols: string[],
        code: string
    ): string {
        return `
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body { font-family: var(--vscode-font-family); padding: 20px; }
                    h2 { color: var(--vscode-foreground); }
                    .code { background: var(--vscode-textCodeBlock-background); padding: 10px; border-radius: 4px; overflow-x: auto; }
                    .symbols { margin-top: 20px; }
                    .symbol { display: inline-block; background: var(--vscode-badge-background); color: var(--vscode-badge-foreground); padding: 2px 8px; border-radius: 12px; margin: 2px; }
                </style>
            </head>
            <body>
                <h2>Explanation</h2>
                <p>${explanation.replace(/\n/g, '<br>')}</p>
                
                <h3>Selected Code</h3>
                <div class="code"><pre><code>${this.escapeHtml(code)}</code></pre></div>
                
                ${symbols.length > 0 ? `
                <div class="symbols">
                    <h3>Referenced Symbols</h3>
                    ${symbols.map(s => `<span class="symbol">${this.escapeHtml(s)}</span>`).join('')}
                </div>
                ` : ''}
            </body>
            </html>
        `;
    }

    private escapeHtml(text: string): string {
        return text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }

    dispose() {
        // Cleanup if needed
    }
}
