# backend/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict
from azure_rag_backend import AzureRAGBackend

app = FastAPI(title="Azure RAG Chat API", version="1.0")

# Initialize Azure RAG backend
rag_backend = AzureRAGBackend()

# Request and response schemas


class ChatRequest(BaseModel):
    query: str
    conversation_id: str = None  # optional multi-turn session


class ChatResponse(BaseModel):
    answer: str
    sources: List[str]


# In-memory session memory
conversation_memory: Dict[str, List[Dict[str, str]]] = {}


@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    """
    Chat endpoint fully backed by Azure.
    Queries go through Azure Cognitive Search + Azure OpenAI.
    """

    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    # Get existing history for multi-turn chat
    history = []
    if request.conversation_id:
        history = conversation_memory.get(request.conversation_id, [])

    # Azure RAG query (stateless for now)
    # If your backend supports passing history to OpenAI for context, add it here
    answer, sources = rag_backend.query(request.query)

    # Save multi-turn history in memory
    if request.conversation_id:
        history.append({"role": "user", "content": request.query})
        history.append({"role": "assistant", "content": answer})
        conversation_memory[request.conversation_id] = history

    return ChatResponse(answer=answer, sources=sources)


@app.get("/health")
def health_check():
    """
    Health check endpoint.
    """
    return {"status": "ok"}
