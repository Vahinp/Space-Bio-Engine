# Azure OpenAI Integration for NASA Bio-Exploration Dashboard

This guide will help you integrate Azure OpenAI with your NASA Bio-Exploration Dashboard for AI-powered chatbot functionality.

## Prerequisites

1. **Azure OpenAI Resource**: You need an active Azure OpenAI resource
2. **Model Deployments**: Deploy the required models in Azure OpenAI Studio

## Step 1: Deploy Models in Azure

1. Go to [Azure OpenAI Studio](https://oai.azure.com/)
2. Select your resource
3. Go to **Deployments** → **Create new deployment**
4. Create these deployments:
   - **Chat Model**: `gpt-4o-mini` (name: `gpt-4o-mini`)
   - **Embeddings Model**: `text-embedding-3-large` (name: `embed-large`)

## Step 2: Get Your Credentials

1. In Azure Portal, go to your OpenAI resource
2. Navigate to **Keys and Endpoint**
3. Copy:
   - **Endpoint**: `https://your-resource.openai.azure.com`
   - **Key 1**: Your API key
   - **API Version**: Use `2024-06-01`

## Step 3: Configure Environment

1. Update `backend/azure_openai.env` with your credentials:

```env
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_API_VERSION=2024-06-01
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=embed-large
```

## Step 4: Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

## Step 5: Test Your Setup

```bash
python setup_azure_openai.py
```

This will test both chat and embeddings functionality.

## Step 6: Run the AI-Enabled Backend

```bash
python app_with_ai.py
```

The server will start on `http://localhost:5000` with these new endpoints:

- `POST /api/chat` - Basic chat with Azure OpenAI
- `POST /api/chat/context` - Chat with paper context from search results
- `POST /api/embed` - Get embeddings for text

## Step 7: Test the Integration

### Test Chat Endpoint

```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"What are the main effects of microgravity on bone density?"}]}'
```

### Test Context-Aware Chat

```bash
curl -X POST http://localhost:5000/api/chat/context \
  -H "Content-Type: application/json" \
  -d '{
    "messages":[{"role":"user","content":"What research exists on space radiation effects?"}],
    "searchQuery": "space radiation effects"
  }'
```

## Frontend Integration

The frontend chatbot (`components/chatbot-panel.tsx`) has been updated to use the new AI backend. It will:

1. Send user messages to `/api/chat/context`
2. Include search context from the current search query
3. Display AI responses with relevant paper information

## Features

### 🤖 AI Chatbot
- **Context-Aware**: Uses search results to provide relevant answers
- **Paper Integration**: References actual papers from your database
- **Smart Responses**: Tailored to space biology research

### 🔍 Enhanced Search
- **Hybrid Search**: Combines keyword search with AI understanding
- **Semantic Search**: Uses embeddings for better paper discovery
- **Contextual Results**: AI helps interpret search results

### 📊 Smart Analytics
- **Research Insights**: AI can analyze trends and patterns
- **Paper Summaries**: Automatic summarization of research findings
- **Question Answering**: Natural language queries about your data

## Troubleshooting

### Common Issues

1. **403 Forbidden**: Check your API key and endpoint
2. **404 Not Found**: Verify deployment names match exactly
3. **429 Rate Limited**: You've hit rate limits, wait or request quota increase
4. **CORS Errors**: Make sure your frontend calls the backend, not Azure directly

### Debug Steps

1. Run the setup test: `python setup_azure_openai.py`
2. Check Azure OpenAI Studio for deployment status
3. Verify environment variables are loaded correctly
4. Test individual endpoints with curl

## Security Notes

- ✅ API keys are kept server-side only
- ✅ Frontend never directly calls Azure OpenAI
- ✅ All requests go through your Flask backend
- ✅ Environment variables are not committed to git

## Next Steps

1. **Deploy to Production**: Use Azure App Service for your backend
2. **Add More Models**: Experiment with different GPT models
3. **Enhanced Context**: Add more sophisticated paper analysis
4. **Vector Search**: Implement semantic search with embeddings
5. **Custom Prompts**: Fine-tune AI responses for your domain

## Support

If you encounter issues:
1. Check the Azure OpenAI documentation
2. Verify your resource quotas and limits
3. Test with the provided setup script
4. Review the Flask backend logs for errors
