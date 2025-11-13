# Quick Start Guide - Azure RAG Backend

This guide will help you get started with the Azure RAG backend in just a few minutes.

## Prerequisites Checklist

Before you begin, make sure you have:

- [ ] Python 3.8 or higher installed
- [ ] An Azure subscription
- [ ] Azure OpenAI service deployed
- [ ] Azure AI Search service created
- [ ] API keys for both services

## 5-Minute Setup

### Step 1: Install Dependencies (1 minute)

```bash
pip install -r requirements.txt
```

### Step 2: Configure Environment (2 minutes)

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` and add your Azure credentials:
   - Get Azure OpenAI endpoint and key from Azure Portal → Azure OpenAI resource
   - Get Azure AI Search endpoint and key from Azure Portal → Search service
   - Update deployment names to match your Azure OpenAI deployments

### Step 3: Initialize the System (1 minute)

```python
from azure_rag_backend import AzureRAGBackend

# Initialize
backend = AzureRAGBackend()

# Create search index (first time only)
backend.create_search_index()
```

### Step 4: Start Using (1 minute)

**Option A: Python Script**
```python
# Ingest a document
backend.ingest_document("meeting_minutes.pdf")

# Ask a question
result = backend.query("What were the main decisions?")
print(result['answer'])
```

**Option B: REST API**
```bash
# Start the server
python api_server.py

# In another terminal, upload a document
curl -X POST http://localhost:8000/ingest \
  -F "file=@meeting_minutes.pdf"

# Query the system
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What were the main decisions?"}'
```

## Common First-Time Issues

### Issue: "No module named 'azure'"
**Solution:** Run `pip install -r requirements.txt`

### Issue: "Unauthorized" or "Authentication failed"
**Solution:** Check your `.env` file has correct Azure credentials

### Issue: "Index not found"
**Solution:** Run `backend.create_search_index()` first

### Issue: "No documents found" when querying
**Solution:** Ingest at least one document before querying

## Next Steps

1. ✅ Read the full [README.md](README.md) for detailed documentation
2. ✅ Check [example_usage.py](example_usage.py) for more examples
3. ✅ Visit `http://localhost:8000/docs` for interactive API documentation
4. ✅ Start ingesting your meeting minutes and asking questions!

## Quick Tips

- **Start Small:** Test with 1-2 small documents first
- **Check Logs:** The system logs helpful information to help debug issues
- **Experiment:** Try different chunk sizes and top_k values for better results
- **Monitor Costs:** Azure OpenAI charges per token, monitor your usage

## Getting Help

If you run into issues:
1. Check the logs for error messages
2. Review the troubleshooting section in README.md
3. Verify your Azure services are properly configured
4. Check that your API keys haven't expired

## Example Workflow

```python
from azure_rag_backend import AzureRAGBackend

# Initialize
backend = AzureRAGBackend()
backend.create_search_index()

# Ingest documents
docs = [
    "meeting_jan.pdf",
    "meeting_feb.pdf",
    "meeting_mar.pdf"
]

for doc in docs:
    backend.ingest_document(doc)
    print(f"✓ Ingested {doc}")

# Ask questions
questions = [
    "What are the common themes?",
    "What decisions were made?",
    "Who attended the meetings?"
]

for q in questions:
    result = backend.query(q)
    print(f"\nQ: {q}")
    print(f"A: {result['answer']}")
    print(f"Sources: {result['sources']}")
```

Happy querying! 🚀
