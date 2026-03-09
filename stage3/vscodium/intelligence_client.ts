// Intelligence Client - Typed HTTP client for IntelligenceAPI

import * as vscode from 'vscode';

export interface ContextChunk {
    file: string;
    start_line: number;
    end_line: number;
    content: string;
    score: number;
    reason: string;
}

export interface ContextResult {
    chunks: ContextChunk[];
    total_tokens_est: number;
}

export interface CompletionResult {
    completion: string;
    context_used: string[];
    model_used: string;
    latency_ms: number;
}

export interface ExplainResult {
    explanation: string;
    symbols_referenced: string[];
    context_used: ContextChunk[];
}

export interface RefactorResult {
    original: string;
    refactored: string;
    diff: string;
    explanation: string;
}

export interface Symbol {
    name: string;
    kind: string;
    file: string;
    line: number;
    col: number;
    docstring?: string;
}

export interface IndexStatus {
    files_indexed: number;
    last_updated: string;
    embedding_model: string;
    index_size_mb: number;
    watching: boolean;
}

export class IntelligenceClient {
    private baseUrl: string;
    private timeout: number = 60000; // 60 second timeout

    constructor(baseUrl: string) {
        this.baseUrl = baseUrl;
    }

    async getContext(
        query: string,
        workspaceRoot: string,
        cursorFile?: string,
        cursorLine?: number,
        maxChunks: number = 10,
        strategy: 'semantic' | 'callgraph' | 'hybrid' = 'hybrid'
    ): Promise<ContextResult | null> {
        try {
            const response = await fetch(`${this.baseUrl}/v1/context`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query,
                    workspace_root: workspaceRoot,
                    cursor_file: cursorFile,
                    cursor_line: cursorLine,
                    max_chunks: maxChunks,
                    strategy
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('APEX: getContext error:', error);
            return null;
        }
    }

    async complete(
        file: string,
        line: number,
        col: number,
        prefix: string,
        suffix: string,
        maxTokens: number = 256
    ): Promise<CompletionResult | null> {
        try {
            const response = await fetch(`${this.baseUrl}/v1/complete`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    file,
                    line,
                    col,
                    prefix,
                    suffix,
                    max_tokens: maxTokens
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('APEX: complete error:', error);
            return null;
        }
    }

    async explain(
        file: string,
        startLine: number,
        endLine: number,
        question?: string
    ): Promise<ExplainResult | null> {
        try {
            const response = await fetch(`${this.baseUrl}/v1/explain`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    file,
                    start_line: startLine,
                    end_line: endLine,
                    question
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('APEX: explain error:', error);
            return null;
        }
    }

    async refactor(
        file: string,
        startLine: number,
        endLine: number,
        instruction: string
    ): Promise<RefactorResult | null> {
        try {
            const response = await fetch(`${this.baseUrl}/v1/refactor`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    file,
                    start_line: startLine,
                    end_line: endLine,
                    instruction
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('APEX: refactor error:', error);
            return null;
        }
    }

    async getSymbols(file: string): Promise<Symbol[]> {
        try {
            const response = await fetch(
                `${this.baseUrl}/v1/symbols?file=${encodeURIComponent(file)}`
            );

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            return data.symbols || [];
        } catch (error) {
            console.error('APEX: getSymbols error:', error);
            return [];
        }
    }

    async getCallGraph(symbol: string, depth: number = 3): Promise<{ callers: Symbol[]; callees: Symbol[]; depth_searched: number }> {
        try {
            const response = await fetch(
                `${this.baseUrl}/v1/callgraph?symbol=${encodeURIComponent(symbol)}&depth=${depth}`
            );

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('APEX: getCallGraph error:', error);
            return { callers: [], callees: [], depth_searched: depth };
        }
    }

    async getIndexStatus(): Promise<IndexStatus> {
        try {
            const response = await fetch(`${this.baseUrl}/v1/index/status`);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('APEX: getIndexStatus error:', error);
            throw error;
        }
    }

    async healthCheck(): Promise<boolean> {
        try {
            const response = await fetch(`${this.baseUrl}/health`, {
                method: 'GET',
                signal: AbortSignal.timeout(5000) // 5 second timeout
            });
            return response.ok;
        } catch {
            return false;
        }
    }

    dispose() {
        // Cleanup if needed
    }
}
