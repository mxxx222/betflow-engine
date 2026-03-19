# 🚀 DeepSeek Coder & Uncensored Setup Guide

## DeepSeek Models

### 1. **DeepSeek Coder**
- **Purpose**: Code generation and assistance
- **Base URL**: `https://api.deepseek.com/v1`
- **Model**: `deepseek-coder`
- **Use Case**: Programming, code completion, debugging

### 2. **DeepSeek Uncensored**
- **Purpose**: Uncensored AI responses
- **Base URL**: `https://api.deepseek.com/v1`
- **Model**: `deepseek-chat` (uncensored variant)
- **Use Case**: Unrestricted AI assistance

---

## 🔑 API Key Setup

### Get API Keys:
1. Visit: https://platform.deepseek.com/
2. Sign up / Login
3. Navigate to API Keys section
4. Create new API key
5. Copy API key (starts with `sk-...`)

---

## 📝 Configuration

### Environment Variables:
```bash
# DeepSeek Coder
DEEPSEEK_CODER_API_KEY=your_coder_api_key_here
DEEPSEEK_CODER_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_CODER_MODEL=deepseek-coder

# DeepSeek Uncensored
DEEPSEEK_UNCENSORED_API_KEY=your_uncensored_api_key_here
DEEPSEEK_UNCENSORED_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_UNCENSORED_MODEL=deepseek-chat
```

---

## 🎯 Cursor IDE Configuration

### Method 1: Via Cursor Settings UI

1. **Open Cursor Settings**
   - Press `Cmd + ,` (Mac) or `Ctrl + ,` (Windows)
   - Navigate to: **Features** → **AI** → **Models**

2. **Add DeepSeek Coder**
   ```
   Model Name: deepseek-coder
   Provider: OpenAI Compatible
   API Key: [YOUR_DEEPSEEK_CODER_API_KEY]
   Base URL: https://api.deepseek.com/v1
   Model ID: deepseek-coder
   ```

3. **Add DeepSeek Uncensored**
   ```
   Model Name: deepseek-uncensored
   Provider: OpenAI Compatible
   API Key: [YOUR_DEEPSEEK_UNCENSORED_API_KEY]
   Base URL: https://api.deepseek.com/v1
   Model ID: deepseek-chat
   ```

### Method 2: Via Settings JSON

**Mac/Linux:**
```bash
nano ~/.cursor/settings.json
```

**Windows:**
```bash
notepad %APPDATA%\Cursor\User\settings.json
```

**Add configuration:**
```json
{
  "cursor.ai.models": [
    {
      "name": "deepseek-coder",
      "provider": "openai",
      "apiKey": "YOUR_DEEPSEEK_CODER_API_KEY",
      "baseURL": "https://api.deepseek.com/v1",
      "model": "deepseek-coder"
    },
    {
      "name": "deepseek-uncensored",
      "provider": "openai",
      "apiKey": "YOUR_DEEPSEEK_UNCENSORED_API_KEY",
      "baseURL": "https://api.deepseek.com/v1",
      "model": "deepseek-chat"
    }
  ]
}
```

---

## 🐍 Python Usage

### DeepSeek Coder:
```python
from openai import OpenAI

client = OpenAI(
    api_key="YOUR_DEEPSEEK_CODER_API_KEY",
    base_url="https://api.deepseek.com/v1"
)

response = client.chat.completions.create(
    model="deepseek-coder",
    messages=[
        {"role": "user", "content": "Write a Python function to calculate fibonacci"}
    ]
)

print(response.choices[0].message.content)
```

### DeepSeek Uncensored:
```python
from openai import OpenAI

client = OpenAI(
    api_key="YOUR_DEEPSEEK_UNCENSORED_API_KEY",
    base_url="https://api.deepseek.com/v1"
)

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "user", "content": "Your prompt here"}
    ]
)

print(response.choices[0].message.content)
```

---

## ✅ Testing

### Test Script:
```bash
python3 test_deepseek.py
```

---

## 📊 Model Comparison

| Model | Purpose | Best For | API Endpoint |
|-------|---------|----------|-------------|
| **DeepSeek Coder** | Code generation | Programming, debugging | `deepseek-coder` |
| **DeepSeek Uncensored** | Unrestricted AI | General purpose, no filters | `deepseek-chat` |
| **Venice Uncensored** | Unrestricted AI | Privacy-focused | `venice-uncensored` |

---

## 🔧 Integration

### Update `.cursorrules`:
```
# DeepSeek Configuration
DEEPSEEK_CODER_API_KEY=your_key_here
DEEPSEEK_CODER_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_CODER_MODEL=deepseek-coder

DEEPSEEK_UNCENSORED_API_KEY=your_key_here
DEEPSEEK_UNCENSORED_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_UNCENSORED_MODEL=deepseek-chat
```

---

## 💡 Usage Tips

### DeepSeek Coder:
- Excellent for code completion
- Great at debugging
- Supports multiple languages
- Fast response times

### DeepSeek Uncensored:
- No content filtering
- Good for creative tasks
- Fast and reliable
- OpenAI-compatible API

---

## 🚨 Security Notes

⚠️ **Keep API Keys Secure:**
- Never commit API keys to Git
- Use environment variables
- Rotate keys regularly
- Monitor usage in DeepSeek dashboard

---

## 📚 Resources

- **DeepSeek Platform**: https://platform.deepseek.com/
- **API Documentation**: https://api-docs.deepseek.com/
- **Model List**: https://platform.deepseek.com/models

---

**✅ Ready to use DeepSeek models!**

