# Azure-Rag-POC
Azure powered RAG solution for document summarisation and transcription

## Overview

This project provides a complete Python backend for a Retrieval-Augmented Generation (RAG) solution designed to process, analyze, and query meeting minutes using Azure services.

### Features

- 📄 **Document Processing**: Support for PDF, DOCX, and TXT files
- 🔍 **Intelligent Chunking**: Text segmentation with configurable overlap for better context
- 🧠 **Vector Embeddings**: Azure OpenAI embeddings for semantic search
- 🔎 **Vector Search**: Azure AI Search for efficient similarity matching
- 💬 **Question Answering**: Context-aware answers using GPT-4
- 🚀 **REST API**: FastAPI-based API for easy integration
- 📊 **Source Attribution**: Answers include source document references

## Architecture

```
Document Upload → Text Extraction → Chunking → Embedding Generation
                                                        ↓
User Query → Query Embedding → Vector Search ← Azure AI Search Index
                                     ↓
                            Context Retrieval
                                     ↓
                            GPT-4 Answer Generation
```

## Prerequisites

- Python 3.8 or higher
- Azure subscription with the following services:
  - Azure OpenAI Service
  - Azure AI Search (formerly Cognitive Search)
- API keys and endpoints for Azure services

## Installation

1. Clone the repository:
```bash
git clone https://github.com/adwgupta/Azure-Rag-POC.git
cd Azure-Rag-POC
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your Azure credentials
```

## Configuration

Edit the `.env` file with your Azure service credentials:

```env
# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
AZURE_OPENAI_API_VERSION=2024-02-01

# Azure AI Search Configuration
AZURE_SEARCH_ENDPOINT=https://your-search-service.search.windows.net
AZURE_SEARCH_API_KEY=your-search-api-key-here
AZURE_SEARCH_INDEX_NAME=minutes-index

# Application Settings
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
MAX_TOKENS=4000
TEMPERATURE=0.7
```

## Usage

### Option 1: Using the Python Backend Directly

```python
from azure_rag_backend import AzureRAGBackend

# Initialize the backend
backend = AzureRAGBackend()

# Create the search index (first time only)
backend.create_search_index()

# Ingest a document
result = backend.ingest_document("meeting_minutes.pdf", "Q1_2024_Meeting")
print(f"Ingested {result['chunks_processed']} chunks")

# Query the system
response = backend.query("What were the key decisions made?")
print(f"Answer: {response['answer']}")
print(f"Sources: {', '.join(response['sources'])}")
```

### Option 2: Using the REST API

1. Start the API server:
```bash
python api_server.py
```

The server will start on `http://localhost:8000`

2. Create the search index:
```bash
curl -X POST http://localhost:8000/create-index
```

3. Ingest a document:
```bash
curl -X POST http://localhost:8000/ingest \
  -F "file=@meeting_minutes.pdf" \
  -F "source_name=Q1_2024_Meeting"
```

4. Query the system:
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What were the key decisions made?",
    "top_k": 5
  }'
```

5. Health check:
```bash
curl http://localhost:8000/health
```

### API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API information |
| `/health` | GET | Health check |
| `/create-index` | POST | Create/update search index |
| `/ingest` | POST | Ingest a document |
| `/query` | POST | Query the RAG system |

## Project Structure

```
Azure-Rag-POC/
├── azure_rag_backend.py    # Core RAG backend implementation
├── api_server.py            # FastAPI REST API server
├── requirements.txt         # Python dependencies
├── .env.example            # Example environment configuration
├── .env                    # Your configuration (create from .env.example)
└── README.md               # This file
```

## Components

### AzureRAGBackend Class

The main backend class that handles:

- **Document Processing**: `read_document()`, `chunk_text()`
- **Embedding Generation**: `generate_embedding()`
- **Document Ingestion**: `ingest_document()`
- **Semantic Search**: `search_similar()`
- **Answer Generation**: `generate_answer()`, `query()`
- **Index Management**: `create_search_index()`

### API Server

FastAPI-based REST API providing:

- Document upload and ingestion
- Question answering with context
- Health monitoring
- Index management

## Supported Document Formats

- **PDF**: `.pdf`
- **Word Documents**: `.docx`, `.doc`
- **Text Files**: `.txt`

## How It Works

1. **Document Ingestion**:
   - Documents are read and text is extracted
   - Text is split into overlapping chunks
   - Each chunk is embedded using Azure OpenAI
   - Embeddings are stored in Azure AI Search

2. **Query Processing**:
   - User question is embedded
   - Vector similarity search finds relevant chunks
   - Retrieved chunks provide context to GPT-4
   - GPT-4 generates a contextual answer

3. **Answer Generation**:
   - Context from top-k most relevant chunks
   - System prompt guides answer format
   - Sources are cited in the response

## Best Practices

- **Chunk Size**: Default 1000 characters works well for most documents
- **Overlap**: 200 character overlap ensures context continuity
- **Top-K**: Retrieve 5-10 chunks for balanced context
- **Temperature**: 0.7 provides good balance between creativity and accuracy

## Troubleshooting

### Common Issues

1. **Authentication Error**: Verify your Azure credentials in `.env`
2. **Index Not Found**: Run `create_search_index()` first
3. **Rate Limiting**: Azure OpenAI has rate limits; add retry logic if needed
4. **Large Documents**: Consider increasing chunk size for very large documents

## Security Notes

- Never commit `.env` file to version control
- Use Azure Key Vault for production deployments
- Implement proper authentication for the API in production
- Configure CORS appropriately for your use case

## Future Enhancements

- [ ] Support for more document formats (PPT, Excel)
- [ ] Batch document processing
- [ ] Multi-language support
- [ ] Advanced filtering and metadata
- [ ] Conversation history and follow-up questions
- [ ] Document summarization endpoint
- [ ] Streaming responses

## License

See LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
