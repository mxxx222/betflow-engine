#!/usr/bin/env python3
"""
Test Venice AI uncensored model connection
"""

import os
import sys
from openai import OpenAI

def test_venice_ai():
    """Test Venice AI API connection"""
    
    # Get API key from environment or use default
    api_key = os.getenv("VENICE_API_KEY", "tDbTCV7ZH9TBtq3-8Wd9QYfk0VxKKX-vObl6amumBz")
    base_url = "https://api.venice.ai/api/v1"
    model = "venice-uncensored"
    
    print("🔍 Testing Venice AI connection...")
    print(f"API Key: {api_key[:20]}...")
    print(f"Base URL: {base_url}")
    print(f"Model: {model}")
    print()
    
    try:
        # Initialize client
        client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        
        # Test 1: List available models
        print("📋 Test 1: Listing available models...")
        models = client.models.list()
        print(f"✅ Found {len(models.data)} models")
        for m in models.data[:5]:  # Show first 5
            print(f"   - {m.id}")
        print()
        
        # Test 2: Simple chat completion
        print("💬 Test 2: Testing chat completion...")
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": "Say hello in one sentence."}
            ],
            max_tokens=50
        )
        
        content = response.choices[0].message.content
        print(f"✅ Response: {content}")
        print()
        
        # Test 3: Uncensored test
        print("🔓 Test 3: Testing uncensored capabilities...")
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": "Explain what 'uncensored AI' means in one sentence."}
            ],
            max_tokens=100
        )
        
        content = response.choices[0].message.content
        print(f"✅ Response: {content}")
        print()
        
        print("✅ All tests passed! Venice AI is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print()
        print("Troubleshooting:")
        print("1. Check API key is correct")
        print("2. Verify internet connection")
        print("3. Check Venice AI service status")
        print("4. Verify model name: venice-uncensored")
        return False

if __name__ == "__main__":
    success = test_venice_ai()
    sys.exit(0 if success else 1)

