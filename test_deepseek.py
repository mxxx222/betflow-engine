#!/usr/bin/env python3
"""
Test DeepSeek Coder and DeepSeek Uncensored models
"""

import os
import sys
from openai import OpenAI

def test_deepseek_coder(api_key: str):
    """Test DeepSeek Coder model"""
    print("\n🔍 Testing DeepSeek Coder...")
    print(f"API Key: {api_key[:20]}...")
    print(f"Base URL: https://api.deepseek.com/v1")
    print(f"Model: deepseek-coder")
    print()
    
    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com/v1"
        )
        
        # Test 1: List models
        print("📋 Test 1: Listing available models...")
        models = client.models.list()
        print(f"✅ Found {len(models.data)} models")
        for m in models.data[:5]:
            print(f"   - {m.id}")
        print()
        
        # Test 2: Code generation
        print("💻 Test 2: Testing code generation...")
        response = client.chat.completions.create(
            model="deepseek-coder",
            messages=[
                {"role": "user", "content": "Write a Python function to calculate the factorial of a number."}
            ],
            max_tokens=200
        )
        
        content = response.choices[0].message.content
        print(f"✅ Response:")
        print(f"{content}")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_deepseek_uncensored(api_key: str):
    """Test DeepSeek Uncensored model"""
    print("\n🔍 Testing DeepSeek Uncensored...")
    print(f"API Key: {api_key[:20]}...")
    print(f"Base URL: https://api.deepseek.com/v1")
    print(f"Model: deepseek-chat")
    print()
    
    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com/v1"
        )
        
        # Test 1: Simple chat
        print("💬 Test 1: Testing chat completion...")
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "user", "content": "Say hello in one sentence."}
            ],
            max_tokens=50
        )
        
        content = response.choices[0].message.content
        print(f"✅ Response: {content}")
        print()
        
        # Test 2: Uncensored capabilities
        print("🔓 Test 2: Testing uncensored capabilities...")
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "user", "content": "Explain what 'uncensored AI' means in one sentence."}
            ],
            max_tokens=100
        )
        
        content = response.choices[0].message.content
        print(f"✅ Response: {content}")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Main test function"""
    print("=" * 60)
    print("🚀 DeepSeek API Test Suite")
    print("=" * 60)
    
    # Get API keys from environment
    coder_key = os.getenv("DEEPSEEK_CODER_API_KEY")
    uncensored_key = os.getenv("DEEPSEEK_UNCENSORED_API_KEY")
    
    if not coder_key:
        print("\n⚠️  DEEPSEEK_CODER_API_KEY not found in environment")
        print("   Set it with: export DEEPSEEK_CODER_API_KEY=your_key")
        coder_key = input("\nEnter DeepSeek Coder API key (or press Enter to skip): ").strip()
    
    if not uncensored_key:
        print("\n⚠️  DEEPSEEK_UNCENSORED_API_KEY not found in environment")
        print("   Set it with: export DEEPSEEK_UNCENSORED_API_KEY=your_key")
        uncensored_key = input("\nEnter DeepSeek Uncensored API key (or press Enter to skip): ").strip()
    
    results = []
    
    # Test DeepSeek Coder
    if coder_key:
        result = test_deepseek_coder(coder_key)
        results.append(("DeepSeek Coder", result))
    else:
        print("\n⏭️  Skipping DeepSeek Coder test (no API key)")
    
    # Test DeepSeek Uncensored
    if uncensored_key:
        result = test_deepseek_uncensored(uncensored_key)
        results.append(("DeepSeek Uncensored", result))
    else:
        print("\n⏭️  Skipping DeepSeek Uncensored test (no API key)")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{name}: {status}")
    
    all_passed = all(result for _, result in results)
    if all_passed:
        print("\n✅ All tests passed! DeepSeek models are working correctly.")
        return 0
    else:
        print("\n❌ Some tests failed. Check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

