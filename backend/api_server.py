"""
FastAPI REST API Server for Azure RAG Backend

This module provides a REST API interface for the Azure RAG backend,
allowing easy integration with frontend applications and external services.

Endpoints:
- POST /ingest: Ingest a document
- POST /query: Query the RAG system
- GET /health: Health check
- POST /create-index: Create or update the search index
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging
import tempfile
import os
from pathlib import Path

from azure_rag_backend import AzureRAGBackend

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Azure RAG Backend API",
    description="REST API for Azure RAG-powered meeting minutes processing",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG backend
rag_backend = None


class QueryRequest(BaseModel):
    """Request model for querying the RAG system."""
    question: str = Field(..., description="The question to ask")
    top_k: int = Field(5, description="Number of context chunks to retrieve", ge=1, le=20)


class QueryResponse(BaseModel):
    """Response model for query results."""
    answer: str
    sources: List[str]
    context: List[Dict[str, Any]]


class ChatMessage(BaseModel):
    """Single chat message used for conversational queries."""
    role: str = Field(..., description="Role of the message: 'user' or 'assistant'")
    content: str = Field(..., description="Message text")


class ChatRequest(BaseModel):
    """Request model for chat-based querying."""
    messages: List[ChatMessage] = Field(..., description="Ordered chat messages")
    top_k: int = Field(5, description="Number of context chunks to retrieve", ge=1, le=20)


class IngestResponse(BaseModel):
    """Response model for document ingestion."""
    source: str
    chunks_processed: int
    status: str


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    message: str


@app.on_event("startup")
async def startup_event():
    """Initialize the RAG backend on startup."""
    global rag_backend
    try:
        logger.info("Initializing Azure RAG Backend...")
        rag_backend = AzureRAGBackend()
        logger.info("Azure RAG Backend initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize RAG backend: {str(e)}")
        raise


@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Azure RAG Backend API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "create_index": "/create-index",
            "ingest": "/ingest",
            "query": "/query"
        }
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Health status of the API
    """
    try:
        if rag_backend is None:
            raise HTTPException(status_code=503, detail="RAG backend not initialized")
        
        return HealthResponse(
            status="healthy",
            message="Azure RAG Backend API is running"
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/create-index", response_model=Dict[str, str])
async def create_index():
    """
    Create or update the Azure AI Search index.
    
    Returns:
        Status of index creation
    """
    try:
        if rag_backend is None:
            raise HTTPException(status_code=503, detail="RAG backend not initialized")
        
        rag_backend.create_search_index()
        
        return {
            "status": "success",
            "message": f"Search index '{rag_backend.index_name}' created/updated successfully"
        }
    except Exception as e:
        logger.error(f"Error creating index: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest", response_model=IngestResponse)
async def ingest_document(
    file: UploadFile = File(...),
    source_name: Optional[str] = Form(None)
):
    """
    Ingest a document into the RAG system.
    
    Args:
        file: Document file to ingest (PDF, DOCX, or TXT)
        source_name: Optional custom name for the source
        
    Returns:
        Ingestion results
    """
    try:
        if rag_backend is None:
            raise HTTPException(status_code=503, detail="RAG backend not initialized")
        
        # Validate file type
        allowed_extensions = ['.pdf', '.docx', '.doc', '.txt']
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # Use filename as source if not provided
            source = source_name if source_name else file.filename
            
            # Ingest the document
            result = rag_backend.ingest_document(tmp_file_path, source)
            
            return IngestResponse(**result)
            
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ingesting document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query", response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    """
    Query the RAG system with a question.
    
    Args:
        request: Query request with question and optional parameters
        
    Returns:
        Answer with sources and context
    """
    try:
        if rag_backend is None:
            raise HTTPException(status_code=503, detail="RAG backend not initialized")
        
        # Process query
        result = rag_backend.query(request.question, top_k=request.top_k)
        
        return QueryResponse(**result)
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat", response_model=QueryResponse)
async def chat_rag(request: ChatRequest):
    """Chat endpoint that keeps prior turns in context while querying RAG."""
    try:
        if rag_backend is None:
            raise HTTPException(status_code=503, detail="RAG backend not initialized")

        result = rag_backend.query_chat(
            [m.model_dump() for m in request.messages],
            top_k=request.top_k
        )

        return QueryResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing chat query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    # Run the API server
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
