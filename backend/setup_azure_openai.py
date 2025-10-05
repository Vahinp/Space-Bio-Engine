#!/usr/bin/env python3
"""
Setup script for Azure OpenAI integration
Run this after configuring your Azure OpenAI resource
"""

import os
import requests
from dotenv import load_dotenv

def test_azure_openai_connection():
    """Test the Azure OpenAI connection"""
    load_dotenv('azure_openai.env')
    
    endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
    api_key = os.getenv('AZURE_OPENAI_API_KEY')
    api_version = os.getenv('AZURE_OPENAI_API_VERSION', '2024-06-01')
    deployment = os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-4o-mini')
    
    if not endpoint or not api_key:
        print("❌ Please configure your Azure OpenAI credentials in backend/azure_openai.env")
        return False
    
    print(f"🔗 Testing connection to: {endpoint}")
    print(f"📦 Using deployment: {deployment}")
    
    # Test chat completion
    url = f"{endpoint}/openai/deployments/{deployment}/chat/completions?api-version={api_version}"
    
    headers = {
        "api-key": api_key,
        "Content-Type": "application/json"
    }
    
    payload = {
        "messages": [{"role": "user", "content": "Say hello in 5 words."}],
        "temperature": 0.2,
        "max_tokens": 50
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            answer = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            print(f"✅ Connection successful!")
            print(f"🤖 AI Response: {answer}")
            return True
        else:
            print(f"❌ Connection failed: {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Connection error: {str(e)}")
        return False

def test_embeddings():
    """Test embeddings endpoint"""
    load_dotenv('azure_openai.env')
    
    endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
    api_key = os.getenv('AZURE_OPENAI_API_KEY')
    api_version = os.getenv('AZURE_OPENAI_API_VERSION', '2024-06-01')
    embedding_deployment = os.getenv('AZURE_OPENAI_EMBEDDING_DEPLOYMENT', 'embed-large')
    
    if not endpoint or not api_key:
        print("❌ Please configure your Azure OpenAI credentials")
        return False
    
    print(f"🔗 Testing embeddings with: {embedding_deployment}")
    
    url = f"{endpoint}/openai/deployments/{embedding_deployment}/embeddings?api-version={api_version}"
    
    headers = {
        "api-key": api_key,
        "Content-Type": "application/json"
    }
    
    payload = {
        "input": "Test embedding for space biology research"
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            embedding = result.get('data', [{}])[0].get('embedding', [])
            print(f"✅ Embeddings successful! Vector length: {len(embedding)}")
            return True
        else:
            print(f"❌ Embeddings failed: {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Embeddings error: {str(e)}")
        return False

def main():
    print("🚀 Azure OpenAI Setup Test")
    print("=" * 50)
    
    # Check if env file exists
    if not os.path.exists('azure_openai.env'):
        print("❌ azure_openai.env file not found!")
        print("Please create it with your Azure OpenAI credentials:")
        print("""
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_API_VERSION=2024-06-01
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=embed-large
        """)
        return
    
    print("1. Testing Chat Completion...")
    chat_success = test_azure_openai_connection()
    
    print("\n2. Testing Embeddings...")
    embed_success = test_embeddings()
    
    print("\n" + "=" * 50)
    if chat_success and embed_success:
        print("🎉 All tests passed! Your Azure OpenAI setup is ready.")
        print("\nNext steps:")
        print("1. Run: python app_with_ai.py")
        print("2. Test the chatbot in your frontend")
    else:
        print("❌ Some tests failed. Please check your configuration.")
        print("\nTroubleshooting:")
        print("- Verify your endpoint URL is correct")
        print("- Check that your API key is valid")
        print("- Ensure your deployments exist in Azure")
        print("- Make sure you have the right permissions")

if __name__ == "__main__":
    main()
