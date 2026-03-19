# 🚀 Venice AI Uncensored Model - Cursor Setup Guide

## Quick Setup (3 Steps)

### Step 1: Open Cursor Settings
1. Open Cursor IDE
2. Press `Cmd + ,` (Mac) or `Ctrl + ,` (Windows/Linux)
3. Navigate to **"Features"** → **"AI"** → **"Models"**

### Step 2: Add Venice AI Model
1. Click **"Add Model"** or **"Custom Model"**
2. Fill in the following:

```
Model Name: venice-uncensored
API Key: tDbTCV7ZH9TBtq3-8Wd9QYfk0VxKKX-vObl6amumBz
Base URL: https://api.venice.ai/api/v1
Model ID: venice-uncensored
```

### Step 3: Verify Connection
1. Click **"Test Connection"** or **"Verify"**
2. If successful, you'll see: ✅ "Connection successful"
3. Select **venice-uncensored** as your default model

---

## Alternative: Via Settings JSON

### Mac/Linux:
```bash
# Edit Cursor settings
open ~/.cursor/settings.json
```

### Windows:
```bash
# Edit Cursor settings
%APPDATA%\Cursor\User\settings.json
```

### Add this configuration:
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

## Available Venice AI Models

### Uncensored Models:
- `venice-uncensored` - Dolphin Mistral 24B Venice Edition (Recommended)
- `dolphin-mistral-24b-venice` - Full model name
- `venice-7b` - Smaller uncensored model

### Other Models:
- `llama-3-70b` - Standard Llama 3
- `mistral-7b` - Mistral base model
- `mixtral-8x7b` - Mixtral model

---

## Usage

### In Cursor:
1. Press `Cmd + K` (Mac) or `Ctrl + K` (Windows) to open AI chat
2. Select **venice-uncensored** from model dropdown
3. Start coding with unrestricted AI assistance

### API Usage (Python):
```python
from openai import OpenAI

client = OpenAI(
    api_key="tDbTCV7ZH9TBtq3-8Wd9QYfk0VxKKX-vObl6amumBz",
    base_url="https://api.venice.ai/api/v1"
)

response = client.chat.completions.create(
    model="venice-uncensored",
    messages=[
        {"role": "user", "content": "Your prompt here"}
    ]
)

print(response.choices[0].message.content)
```

---

## Features

✅ **Uncensored Responses** - No content filtering
✅ **Private** - No data logging or storage
✅ **OpenAI Compatible** - Drop-in replacement
✅ **Free Tier Available** - Via VVV staking
✅ **High Performance** - Fast response times

---

## Troubleshooting

### Connection Failed:
- Check API key is correct
- Verify base URL: `https://api.venice.ai/api/v1`
- Check internet connection
- Try different Venice model name

### Model Not Found:
- Use exact model name: `venice-uncensored`
- Check Venice AI documentation for latest models
- Verify API key has access to model

### Rate Limits:
- Venice AI has rate limits based on staking
- Consider upgrading VVV staking for higher limits
- Check Venice AI dashboard for usage stats

---

## Security Notes

⚠️ **Keep API Key Secure:**
- Never commit API key to Git
- Use environment variables in production
- Rotate keys regularly
- Monitor usage in Venice AI dashboard

---

## Resources

- **Venice AI Docs**: https://docs.venice.ai
- **Venice AI Blog**: https://venice.ai/blog
- **API Reference**: https://docs.venice.ai/api-reference
- **Model List**: https://docs.venice.ai/models

---

## Quick Test

Test Venice AI connection:

```bash
curl https://api.venice.ai/api/v1/models \
  -H "Authorization: Bearer tDbTCV7ZH9TBtq3-8Wd9QYfk0VxKKX-vObl6amumBz"
```

Expected response: List of available models including `venice-uncensored`

---

**✅ Setup Complete!** You can now use Venice AI uncensored model in Cursor.

