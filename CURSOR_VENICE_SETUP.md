# ✅ Venice AI Uncensored - Cursor Setup (QUICK)

## ✅ Test Results
**Status**: ✅ Working perfectly!
- API Key: Valid
- Model: `venice-uncensored` available
- Connection: Successful
- Response: Uncensored AI ready

---

## 🚀 Quick Setup (2 Minutes)

### Method 1: Cursor Settings UI (Easiest)

1. **Open Cursor Settings**
   - Press `Cmd + ,` (Mac) or `Ctrl + ,` (Windows)

2. **Navigate to AI Models**
   - Go to: **Features** → **AI** → **Models**

3. **Add Custom Model**
   ```
   Model Name: venice-uncensored
   Provider: OpenAI Compatible
   API Key: tDbTCV7ZH9TBtq3-8Wd9QYfk0VxKKX-vObl6amumBz
   Base URL: https://api.venice.ai/api/v1
   Model ID: venice-uncensored
   ```

4. **Set as Default**
   - Select `venice-uncensored` from model dropdown
   - Click "Set as Default"

5. **Test**
   - Press `Cmd + K` to open AI chat
   - Type: "Hello, Venice AI!"
   - Should respond immediately ✅

---

### Method 2: Settings JSON (Advanced)

**Mac/Linux:**
```bash
nano ~/.cursor/settings.json
```

**Windows:**
```bash
notepad %APPDATA%\Cursor\User\settings.json
```

**Add this:**
```json
{
  "cursor.ai.models": [
    {
      "name": "venice-uncensored",
      "provider": "openai",
      "apiKey": "tDbTCV7ZH9TBtq3-8Wd9QYfk0VxKKX-vObl6amumBz",
      "baseURL": "https://api.venice.ai/api/v1",
      "model": "venice-uncensored"
    }
  ],
  "cursor.ai.defaultModel": "venice-uncensored"
}
```

---

## 🎯 Usage

### In Cursor:
1. Press `Cmd + K` (Mac) or `Ctrl + K` (Windows)
2. Select `venice-uncensored` from dropdown
3. Start coding with unrestricted AI!

### Features:
- ✅ **Uncensored** - No content filtering
- ✅ **Private** - No data logging
- ✅ **Fast** - Low latency responses
- ✅ **Free Tier** - Via VVV staking

---

## 📊 Available Models

Tested and working:
- ✅ `venice-uncensored` - **Recommended** (Dolphin Mistral 24B)
- ✅ `qwen3-4b` - Smaller model
- ✅ `mistral-31-24b` - Mistral variant
- ✅ `qwen3-235b` - Large model

---

## ✅ Verification

Run test script:
```bash
python3 test_venice_ai.py
```

Expected output:
```
✅ All tests passed! Venice AI is working correctly.
```

---

## 🔧 Troubleshooting

### Model Not Found:
- Use exact name: `venice-uncensored`
- Check base URL: `https://api.venice.ai/api/v1`
- Verify API key is correct

### Connection Failed:
- Check internet connection
- Verify API key hasn't expired
- Try restarting Cursor

### Rate Limits:
- Check Venice AI dashboard
- Consider VVV staking for higher limits
- Monitor usage stats

---

## 📝 Notes

- API key is already configured in `.cursorrules`
- Test script confirms connection works
- `ai_service.py` updated to use Venice AI
- All Python code ready to use Venice AI

---

**✅ Setup Complete!** Venice AI uncensored is ready to use in Cursor.

