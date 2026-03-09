#!/usr/bin/env python3
"""
Token Calculator for JSON Files
Estimates token count and adds _token_estimate field to each JSON file
"""

import json
import os
from pathlib import Path

# Token estimation: ~4 chars per token (average for code)
CHARS_PER_TOKEN = 4


def estimate_tokens(text: str) -> int:
    """Estimate token count from text."""
    return max(1, len(text) // CHARS_PER_TOKEN)


def process_json_file(filepath: Path) -> dict:
    """Process a JSON file and add token estimate."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse JSON to validate
        data = json.loads(content)
        
        # Calculate token estimate
        token_estimate = estimate_tokens(content)
        
        # Add token metadata
        if isinstance(data, dict):
            data['_token_estimate'] = token_estimate
            data['_token_metadata'] = {
                'char_count': len(content),
                'estimated_tokens': token_estimate,
                'calculation': f"chars / {CHARS_PER_TOKEN}"
            }
        
        return {
            'file': str(filepath),
            'tokens': token_estimate,
            'chars': len(content),
            'success': True
        }
    except Exception as e:
        return {
            'file': str(filepath),
            'error': str(e),
            'success': False
        }


def scan_directory(root_dir: Path) -> list:
    """Scan directory for JSON files and add token estimates."""
    results = []
    json_files = list(root_dir.rglob('*.json'))
    
    print(f"Found {len(json_files)} JSON files")
    print("=" * 60)
    
    for filepath in json_files:
        # Skip node_modules and build directories
        if 'node_modules' in str(filepath) or 'dist' in str(filepath):
            continue
            
        result = process_json_file(filepath)
        results.append(result)
        
        if result['success']:
            print(f"[OK] {filepath.name}: {result['tokens']:,} tokens ({result['chars']:,} chars)")
        else:
            print(f"[ERR] {filepath.name}: {result.get('error', 'Unknown error')}")
    
    return results


def generate_token_manifest(results: list, output_path: Path):
    """Generate a manifest file with all token counts."""
    manifest = {
        'total_files': len([r for r in results if r['success']]),
        'total_tokens': sum([r['tokens'] for r in results if r['success']]),
        'files': [
            {
                'path': r['file'],
                'tokens': r['tokens'],
                'chars': r.get('chars', 0)
            }
            for r in results if r['success']
        ]
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
    
    print("=" * 60)
    print(f"Total tokens: {manifest['total_tokens']:,}")
    print(f"Manifest saved to: {output_path}")
    
    return manifest


if __name__ == '__main__':
    # Scan current project
    root = Path(__file__).parent
    results = scan_directory(root)
    
    # Generate manifest
    manifest_path = root / 'token_manifest.json'
    manifest = generate_token_manifest(results, manifest_path)
