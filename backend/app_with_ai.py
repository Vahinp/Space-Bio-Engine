#!/usr/bin/env python3

import os
import json
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from database import get_all_papers_from_db
from elasticsearch_service import ElasticsearchService

# Load environment variables
load_dotenv('azure_openai.env')

app = Flask(__name__)
CORS(app)

# Azure OpenAI configuration
AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
AZURE_OPENAI_API_KEY = os.getenv('AZURE_OPENAI_API_KEY')
AZURE_OPENAI_API_VERSION = os.getenv('AZURE_OPENAI_API_VERSION', '2024-06-01')
AZURE_OPENAI_DEPLOYMENT = os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-4o-mini')
AZURE_OPENAI_EMBEDDING_DEPLOYMENT = os.getenv('AZURE_OPENAI_EMBEDDING_DEPLOYMENT', 'embed-large')

# Initialize Elasticsearch service
es_service = ElasticsearchService()

@app.route('/')
def home():
    return jsonify({
        "message": "NASA Bio-Exploration Dashboard API with AI",
        "version": "2.0",
        "endpoints": {
            "papers": "/api/papers",
            "search": "/api/search",
            "chat": "/api/chat",
            "embed": "/api/embed"
        }
    })

@app.route('/api/papers')
def get_papers():
    """Get all papers from database"""
    try:
        papers = get_all_papers_from_db()
        return jsonify({
            "papers": papers,
            "total": len(papers)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/search', methods=['POST'])
def search_papers():
    """Search papers using Elasticsearch"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        filters = data.get('filters', {})
        
        # Use Elasticsearch service for search
        results = es_service.search_papers(query, filters)
        
        return jsonify({
            "papers": results.get('papers', []),
            "total": results.get('total', 0),
            "query": query
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat_with_ai():
    """Chat with Azure OpenAI"""
    try:
        data = request.get_json()
        messages = data.get('messages', [])
        
        if not messages:
            return jsonify({"error": "No messages provided"}), 400
        
        # Prepare Azure OpenAI request
        url = f"{AZURE_OPENAI_ENDPOINT}/openai/deployments/{AZURE_OPENAI_DEPLOYMENT}/chat/completions?api-version={AZURE_OPENAI_API_VERSION}"
        
        headers = {
            "api-key": AZURE_OPENAI_API_KEY,
            "Content-Type": "application/json"
        }
        
        payload = {
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 512
        }
        
        # Make request to Azure OpenAI
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code != 200:
            return jsonify({
                "error": "Azure OpenAI request failed",
                "details": response.json()
            }), 500
        
        result = response.json()
        answer = result.get('choices', [{}])[0].get('message', {}).get('content', '')
        
        return jsonify({
            "answer": answer,
            "usage": result.get('usage', {})
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/embed', methods=['POST'])
def get_embeddings():
    """Get embeddings from Azure OpenAI"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({"error": "No text provided"}), 400
        
        # Prepare Azure OpenAI embeddings request
        url = f"{AZURE_OPENAI_ENDPOINT}/openai/deployments/{AZURE_OPENAI_EMBEDDING_DEPLOYMENT}/embeddings?api-version={AZURE_OPENAI_API_VERSION}"
        
        headers = {
            "api-key": AZURE_OPENAI_API_KEY,
            "Content-Type": "application/json"
        }
        
        payload = {
            "input": text
        }
        
        # Make request to Azure OpenAI
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code != 200:
            return jsonify({
                "error": "Azure OpenAI embeddings request failed",
                "details": response.json()
            }), 500
        
        result = response.json()
        embedding = result.get('data', [{}])[0].get('embedding', [])
        
        return jsonify({
            "vector": embedding,
            "usage": result.get('usage', {})
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat/context', methods=['POST'])
def chat_with_context():
    """Chat with AI using paper context from search results"""
    try:
        data = request.get_json()
        messages = data.get('messages', [])
        search_query = data.get('searchQuery', '')
        
        # Get relevant papers for context
        context_papers = []
        if search_query:
            search_results = es_service.search_papers(search_query, {})
            context_papers = search_results.get('papers', [])[:5]  # Top 5 papers
        
        # Create context from papers
        context = ""
        if context_papers:
            context = "Relevant papers from the NASA Bio-Exploration database:\n\n"
            for i, paper in enumerate(context_papers, 1):
                context += f"{i}. {paper.get('title', 'Unknown Title')}\n"
                context += f"   Year: {paper.get('year', 'Unknown')}\n"
                if paper.get('abstract'):
                    context += f"   Abstract: {paper.get('abstract', '')[:200]}...\n"
                context += "\n"
        
        # Add context to the conversation
        system_message = {
            "role": "system",
            "content": f"""You are an AI assistant for the NASA Bio-Exploration Dashboard. 
            You help researchers understand space biology research papers and trends.
            {context}
            
            When answering questions, refer to the relevant papers when appropriate.
            Be helpful, accurate, and concise in your responses."""
        }
        
        # Prepare messages with context
        full_messages = [system_message] + messages
        
        # Call Azure OpenAI
        url = f"{AZURE_OPENAI_ENDPOINT}/openai/deployments/{AZURE_OPENAI_DEPLOYMENT}/chat/completions?api-version={AZURE_OPENAI_API_VERSION}"
        
        headers = {
            "api-key": AZURE_OPENAI_API_KEY,
            "Content-Type": "application/json"
        }
        
        payload = {
            "messages": full_messages,
            "temperature": 0.2,
            "max_tokens": 1024
        }
        
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code != 200:
            return jsonify({
                "error": "Azure OpenAI request failed",
                "details": response.json()
            }), 500
        
        result = response.json()
        answer = result.get('choices', [{}])[0].get('message', {}).get('content', '')
        
        return jsonify({
            "answer": answer,
            "context_papers": len(context_papers),
            "usage": result.get('usage', {})
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting NASA Bio-Exploration Dashboard API with AI...")
    print(f"Azure OpenAI Endpoint: {AZURE_OPENAI_ENDPOINT}")
    print(f"Azure OpenAI Deployment: {AZURE_OPENAI_DEPLOYMENT}")
    app.run(debug=True, port=5000)
