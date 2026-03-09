// Status Bar - Model, index, and VRAM status display

import * as vscode from 'vscode';
import { IndexStatus } from './intelligence_client';

export class StatusBar {
    private statusBarItem: vscode.StatusBarItem;
    private state: 'disconnected' | 'connecting' | 'connected' | 'loading' | 'error' = 'disconnected';
    private indexStatus: IndexStatus | null = null;

    constructor() {
        this.statusBarItem = vscode.window.createStatusBarItem(
            vscode.StatusBarAlignment.Right,
            100
        );
        this.statusBarItem.command = 'apex.showStatus';
        this.statusBarItem.show();
        this.updateDisconnected();
    }

    updateDisconnected(): void {
        this.state = 'disconnected';
        this.statusBarItem.text = '$(circle-outline) APEX';
        this.statusBarItem.tooltip = 'APEX: Disconnected from intelligence server';
        this.statusBarItem.color = undefined;
    }

    updateConnecting(): void {
        this.state = 'connecting';
        this.statusBarItem.text = '$(sync~spin) APEX';
        this.statusBarItem.tooltip = 'APEX: Connecting to intelligence server...';
        this.statusBarItem.color = undefined;
    }

    updateConnected(): void {
        this.state = 'connected';
        let text = '$(check) APEX';
        
        if (this.indexStatus) {
            text += ` | ${this.indexStatus.files_indexed} files`;
        }

        this.statusBarItem.text = text;
        this.statusBarItem.tooltip = this.buildTooltip();
        this.statusBarItem.color = undefined;
    }

    updateLoading(): void {
        this.state = 'loading';
        this.statusBarItem.text = '$(sync~spin) APEX';
        this.statusBarItem.tooltip = 'APEX: Processing request...';
        this.statusBarItem.color = undefined;
    }

    updateError(message?: string): void {
        this.state = 'error';
        this.statusBarItem.text = '$(error) APEX';
        this.statusBarItem.tooltip = message || 'APEX: Error connecting to intelligence server';
        this.statusBarItem.color = new vscode.ThemeColor('statusBarItem.errorForeground');
    }

    updateIndexStatus(status: IndexStatus): void {
        this.indexStatus = status;
        
        if (this.state === 'connected' || this.state === 'loading') {
            this.updateConnected();
        }
    }

    private buildTooltip(): string {
        let tooltip = 'APEX AI Code Intelligence\n\n';
        tooltip += `Status: ${this.getStateLabel()}\n`;

        if (this.indexStatus) {
            tooltip += `\n---\n\n`;
            tooltip += `Files Indexed: ${this.indexStatus.files_indexed}\n`;
            tooltip += `Index Size: ${this.indexStatus.index_size_mb.toFixed(1)} MB\n`;
            tooltip += `Embedding Model: ${this.indexStatus.embedding_model}\n`;
            tooltip += `Last Updated: ${this.formatDate(this.indexStatus.last_updated)}\n`;
            tooltip += `Watching: ${this.indexStatus.watching ? 'Yes' : 'No'}\n`;
        }

        tooltip += `\n---\n\n`;
        tooltip += `Commands:\n`;
        tooltip += `• Ctrl+Shift+A: Trigger completion\n`;
        tooltip += `• Ctrl+Shift+E: Explain selection\n`;
        tooltip += `• Ctrl+Shift+R: Refactor code\n`;

        return tooltip;
    }

    private getStateLabel(): string {
        switch (this.state) {
            case 'disconnected': return 'Disconnected';
            case 'connecting': return 'Connecting...';
            case 'connected': return 'Connected';
            case 'loading': return 'Processing...';
            case 'error': return 'Error';
            default: return 'Unknown';
        }
    }

    private formatDate(dateString: string): string {
        if (!dateString) return 'Never';
        try {
            const date = new Date(dateString);
            return date.toLocaleString();
        } catch {
            return dateString;
        }
    }

    showStatus(): void {
        vscode.window.showInformationMessage(this.buildTooltip());
    }

    dispose(): void {
        this.statusBarItem.dispose();
    }
}
