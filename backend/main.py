# backend/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse 
from typing import Optional
from pydantic import BaseModel
from typing import List, Dict
from backend.azure_rag_backend import AzureRAGBackend



app = FastAPI(title="Azure RAG Chat API", version="1.0")

# Add CORS middleware FIRST (must be before routes in the middleware stack)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Initialize Azure RAG backend
rag_backend = AzureRAGBackend()
print(">>> LOADED main.py WITH CORS <<<")



# Request and response schemas


class ChatRequest(BaseModel): 
    query: str 
    conversation_id: Optional[str] = None

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
    result = rag_backend.query(request.query)
    answer = result["answer"]
    sources = result["sources"]

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
