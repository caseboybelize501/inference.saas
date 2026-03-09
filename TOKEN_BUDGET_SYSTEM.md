# APEX Token Budget System

**Implemented:** March 9, 2026

---

## ✅ What Was Built

### 1. Token Calculator (`calculate_tokens.py`)
Scans all JSON files in the project and adds token estimates:
- **Token estimation:** `chars / 4` (average for code)
- **Adds to each JSON:** `_token_estimate` and `_token_metadata` fields
- **Generates:** `token_manifest.json` with all file token counts

### 2. Token Manifest (`token_manifest.json`)
```json
{
  "total_files": 10,
  "total_tokens": 19,643,
  "files": [
    {
      "path": ".../package.json",
      "tokens": 1222,
      "chars": 4890
    },
    ...
  ]
}
```

### 3. Chat Sidebar Token Budget Display
- **Real-time tracking** of context tokens
- **Visual progress bar** showing usage percentage
- **Color-coded warnings:**
  - 🟢 Green: < 70% usage
  - 🟡 Yellow: 70-90% usage
  - 🔴 Red: > 90% usage

### 4. Context Budget Enforcement
- **Max context:** 32,768 tokens (configurable)
- **Auto-reject** if budget exceeded
- **Shows breakdown:** Prompt tokens + File tokens = Total

---

## 🎯 How It Works

### User Flow

1. **User types message** in chat
2. **Extension calculates:**
   - `promptTokens = message.length / 4`
   - `fileTokens = token_manifest[selected_file]` (if file referenced)
   - `totalContext = promptTokens + fileTokens`
3. **Budget check:**
   - If `totalContext > 32,768` → **Reject with warning**
   - If `totalContext <= 32,768` → **Send to llama-server**
4. **Display updates:**
   - Token budget bar appears
   - Shows: "Context: X / 32,768 tokens"
   - Color changes based on usage

---

## 📊 Example Token Counts

| File Type | Example | Tokens |
|-----------|---------|--------|
| VSCode settings | `.vscode/settings.json` | 230 |
| Package.json | `stage3/vscodium/package.json` | 1,222 |
| Package-lock | `package-lock.json` | 16,012 |
| Model config | `model_config.json` | 1,074 |
| **Total project** | All JSON files | **19,643** |

---

## 🔧 Configuration

### Change Max Context

Edit `sidebar_chat.ts`:
```typescript
private readonly MAX_CONTEXT_TOKENS: number = 32768; // Change this
```

### Token Estimation Formula

Edit `calculate_tokens.py`:
```python
CHARS_PER_TOKEN = 4  # Adjust for your model
```

Common values:
- **English text:** 4-5 chars/token
- **Code:** 3-4 chars/token
- **Chinese/Japanese:** 1-2 chars/token

---

## 🚀 Usage

### In VSCode Chat

1. **Open APEX chat** (right sidebar 🤖 icon)
2. **Type a message:** "Explain this file"
3. **Select code** in editor (optional)
4. **Token budget appears:**
   ```
   Context: 1,250 / 32,768 tokens
   Prompt: 1,200  File: 50
   [████████████░░░░░░░░] 38%
   ```
5. **Send** → APEX decides if context fits

### Budget Scenarios

| Scenario | Prompt | File | Total | Decision |
|----------|--------|------|-------|----------|
| Simple Q | 500 | 0 | 500 | ✅ Answer |
| File reference | 200 | 1,222 | 1,422 | ✅ Answer |
| Large context | 5,000 | 16,012 | 21,012 | ✅ Answer |
| Too large | 10,000 | 25,000 | 35,000 | ❌ Reject |

---

## ⚙️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│  VSCode Chat Sidebar                                    │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Token Budget Display                            │   │
│  │  Context: 1,250 / 32,768 tokens [████░░] 38%    │   │
│  └─────────────────────────────────────────────────┘   │
│                         │                                │
│                         ▼                                │
│  ┌─────────────────────────────────────────────────┐   │
│  │  sidebar_chat.ts                                 │   │
│  │  - estimatePromptTokens()                        │   │
│  │  - getFileTokenCount() ← token_manifest.json    │   │
│  │  - Check: total > MAX_CONTEXT_TOKENS?            │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  llama-server:8080   │
              │  (if context fits)   │
              └──────────────────────┘
```

---

## 📝 Files Modified

| File | Changes |
|------|---------|
| `calculate_tokens.py` | NEW - Token calculator script |
| `token_manifest.json` | NEW - Token metadata for all JSON files |
| `stage3/vscodium/sidebar_chat.ts` | Token budget UI + logic |
| `stage3/vscodium/package.json` | No changes (already updated) |

---

## 🎯 Next Steps

### Phase 1: ✅ Complete
- [x] Calculate tokens for JSON files
- [x] Generate token manifest
- [x] Display token budget in chat
- [x] Enforce context limit

### Phase 2: Future Enhancements
- [ ] Calculate tokens for ALL file types (.py, .ts, .md, etc.)
- [ ] Real-time token counting as user types
- [ ] Suggest context reduction strategies
- [ ] Per-file token caching
- [ ] Token budget history across conversations

---

## 🧪 Testing

### Test Context Budget

1. **Small context (should pass):**
   ```
   Message: "What does this file do?"
   Selected: package.json (1,222 tokens)
   Expected: ~1,250 tokens total → ✅ Answer
   ```

2. **Large context (should fail):**
   ```
   Message: [Paste 50,000 chars of text]
   Expected: ~12,500+ tokens → ⚠️ Warning if > 32K
   ```

3. **File reference:**
   ```
   Message: "Explain this"
   Selected: Large file
   Expected: Shows file token count in budget
   ```

---

**Status:** ✅ Token budget system implemented and active!
