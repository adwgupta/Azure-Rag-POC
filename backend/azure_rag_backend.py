"""
Azure RAG Backend for Meeting Minutes Processing

This module provides a comprehensive backend for a Retrieval-Augmented Generation (RAG)
solution designed to process, store, and query meeting minutes using Azure services.

Features:
- Document ingestion and processing (PDF, DOCX, TXT)
- Text chunking with overlap for better context
- Vector embeddings using Azure OpenAI
- Vector storage and retrieval using Azure AI Search
- Question-answering capabilities with context retrieval
"""

import os
import logging
from typing import List, Dict, Optional, Any
from pathlib import Path

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    VectorSearch,
    VectorSearchProfile,
    HnswAlgorithmConfiguration,
)
from openai import AzureOpenAI
from dotenv import load_dotenv

# Document processing
import pypdf
from docx import Document as DocxDocument

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AzureRAGBackend:
    """
    Azure RAG Backend for processing and querying meeting minutes.
    
    This class handles:
    - Document processing and chunking
    - Embedding generation via Azure OpenAI
    - Vector storage in Azure AI Search
    - Semantic search and retrieval
    - Answer generation with retrieved context
    """
    
    def __init__(self):
        """Initialize the Azure RAG Backend with configuration from environment."""
        load_dotenv()
        
        # Azure OpenAI configuration
        self.openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.openai_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-35-turbo")
        self.embedding_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-ada-002")
        self.api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")
        
        # Azure AI Search configuration
        self.search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        self.search_api_key = os.getenv("AZURE_SEARCH_API_KEY")
        self.index_name = os.getenv("AZURE_SEARCH_INDEX_NAME", "ragpocmeet")
        
        # Application settings
        self.chunk_size = int(os.getenv("CHUNK_SIZE", "1000"))
        self.chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "200"))
        self.max_tokens = int(os.getenv("MAX_TOKENS", "4000"))
        self.temperature = float(os.getenv("TEMPERATURE", "0.7"))
        
        # Initialize clients
        self._initialize_clients()
        
    def _initialize_clients(self):
        """Initialize Azure OpenAI and Azure AI Search clients."""
        try:
            # Initialize Azure OpenAI client
            self.openai_client = AzureOpenAI(
                azure_endpoint=self.openai_endpoint,
                api_key=self.openai_api_key,
                api_version=self.api_version
            )
            logger.info("Azure OpenAI client initialized successfully")
            
            # Initialize Azure AI Search clients
            self.search_index_client = SearchIndexClient(
                endpoint=self.search_endpoint,
                credential=AzureKeyCredential(self.search_api_key)
            )
            
            self.search_client = SearchClient(
                endpoint=self.search_endpoint,
                index_name=self.index_name,
                credential=AzureKeyCredential(self.search_api_key)
            )
            logger.info("Azure AI Search clients initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing clients: {str(e)}")
            raise
    
    def create_search_index(self):
        """
        Create or update the Azure AI Search index for storing document chunks and embeddings.
        """
        try:
            fields = [
                SearchField(
                    name="id",
                    type=SearchFieldDataType.String,
                    key=True,
                    filterable=True
                ),
                SearchField(
                    name="content",
                    type=SearchFieldDataType.String,
                    searchable=True
                ),
                SearchField(
                    name="source",
                    type=SearchFieldDataType.String,
                    filterable=True,
                    facetable=True
                ),
                SearchField(
                    name="chunk_id",
                    type=SearchFieldDataType.Int32,
                    filterable=True
                ),
                SearchField(
                    name="embedding",
                    type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                    vector_search_dimensions=1536,
                    vector_search_profile_name="my-vector-profile"
                ),
            ]
            
            # Configure vector search
            vector_search = VectorSearch(
                algorithms=[
                    HnswAlgorithmConfiguration(name="my-hnsw-config")
                ],
                profiles=[
                    VectorSearchProfile(
                        name="my-vector-profile",
                        algorithm_configuration_name="my-hnsw-config"
                    )
                ]
            )
            
            # Create the search index
            index = SearchIndex(
                name=self.index_name,
                fields=fields,
                vector_search=vector_search
            )
            
            result = self.search_index_client.create_or_update_index(index)
            logger.info(f"Search index '{self.index_name}' created/updated successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error creating search index: {str(e)}")
            raise
    
    def read_document(self, file_path: str) -> str:
        """
        Read and extract text from various document formats.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Extracted text content
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            if file_path.suffix.lower() == '.pdf':
                return self._read_pdf(file_path)
            elif file_path.suffix.lower() in ['.docx', '.doc']:
                return self._read_docx(file_path)
            elif file_path.suffix.lower() == '.txt':
                return self._read_txt(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_path.suffix}")
                
        except Exception as e:
            logger.error(f"Error reading document {file_path}: {str(e)}")
            raise
    
    def _read_pdf(self, file_path: Path) -> str:
        """Extract text from PDF file."""
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = pypdf.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text
    
    def _read_docx(self, file_path: Path) -> str:
        """Extract text from DOCX file."""
        doc = DocxDocument(file_path)
        return "\n".join([paragraph.text for paragraph in doc.paragraphs])
    
    def _read_txt(self, file_path: Path) -> str:
        """Read text from TXT file."""
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    
    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks for better context preservation.
        
        Args:
            text: Input text to chunk
            
        Returns:
            List of text chunks
        """
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + self.chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start += self.chunk_size - self.chunk_overlap
        
        logger.info(f"Text split into {len(chunks)} chunks")
        return chunks
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate vector embedding for text using Azure OpenAI.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        try:
            response = self.openai_client.embeddings.create(
                input=text,
                model=self.embedding_deployment
            )
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise
    
    def ingest_document(self, file_path: str, source_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Ingest a document: read, chunk, embed, and store in Azure AI Search.
        
        Args:
            file_path: Path to the document
            source_name: Optional name for the source (defaults to filename)
            
        Returns:
            Dictionary with ingestion results
        """
        try:
            # Read document
            logger.info(f"Reading document: {file_path}")
            text = self.read_document(file_path)
            
            # Chunk text
            chunks = self.chunk_text(text)
            
            # Use filename as source if not provided
            if source_name is None:
                source_name = Path(file_path).name
            
            # Process and upload chunks
            documents = []
            for idx, chunk in enumerate(chunks):
                # Generate embedding
                embedding = self.generate_embedding(chunk)
                
                # Create document
                doc = {
                    "id": f"{source_name}_{idx}",
                    "content": chunk,
                    "source": source_name,
                    "chunk_id": idx,
                    "embedding": embedding
                }
                documents.append(doc)
                
                logger.info(f"Processed chunk {idx + 1}/{len(chunks)}")
            
            # Upload to Azure AI Search
            result = self.search_client.upload_documents(documents=documents)
            logger.info(f"Successfully ingested {len(documents)} chunks from {source_name}")
            
            return {
                "source": source_name,
                "chunks_processed": len(documents),
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error ingesting document: {str(e)}")
            raise
    
    def search_similar(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar document chunks using vector similarity.
        
        Args:
            query: Search query
            top_k: Number of top results to return
            
        Returns:
            List of similar document chunks with metadata
        """
        try:
            # Generate embedding for the query
            query_embedding = self.generate_embedding(query)
            
            # Perform vector search
            results = self.search_client.search(
                search_text=None,
                vector_queries=[{
                    "vector": query_embedding,
                    "k_nearest_neighbors": top_k,
                    "fields": "embedding"
                }],
                select=["id", "content", "source", "chunk_id"]
            )
            
            # Collect results
            search_results = []
            for result in results:
                search_results.append({
                    "id": result["id"],
                    "content": result["content"],
                    "source": result["source"],
                    "chunk_id": result["chunk_id"],
                    "score": result.get("@search.score", 0)
                })
            
            logger.info(f"Found {len(search_results)} similar chunks for query")
            return search_results
            
        except Exception as e:
            logger.error(f"Error performing search: {str(e)}")
            raise
    
    def generate_answer(self, query: str, context_chunks: List[Dict[str, Any]]) -> str:
        """
        Generate an answer using Azure OpenAI with retrieved context.
        
        Args:
            query: User's question
            context_chunks: Retrieved context chunks
            
        Returns:
            Generated answer
        """
        try:
            # Prepare context from chunks
            context = "\n\n".join([
                f"[Source: {chunk['source']}, Chunk: {chunk['chunk_id']}]\n{chunk['content']}"
                for chunk in context_chunks
            ])
            
            # Create prompt
            system_message = """You are an AI assistant helping to answer questions about meeting minutes and documents.
Use the provided context to answer the user's question accurately and concisely.
If the context doesn't contain enough information to answer the question, say so.
Always cite the source documents when providing information."""
            
            user_message = f"""Context from documents:
{context}

Question: {query}

Please provide a comprehensive answer based on the context above."""
            
            # Generate response
            response = self.openai_client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            answer = response.choices[0].message.content
            logger.info("Successfully generated answer")
            return answer
            
        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}")
            raise
    
    def query(self, question: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Complete RAG query: search for relevant context and generate answer.
        
        Args:
            question: User's question
            top_k: Number of context chunks to retrieve
            
        Returns:
            Dictionary with answer and sources
        """
        try:
            # Search for relevant chunks
            logger.info(f"Processing query: {question}")
            context_chunks = self.search_similar(question, top_k=top_k)
            
            if not context_chunks:
                return {
                    "answer": "I couldn't find any relevant information in the documents to answer your question.",
                    "sources": [],
                    "context": []
                }
            
            # Generate answer
            answer = self.generate_answer(question, context_chunks)
            
            # Extract unique sources
            sources = list(set([chunk["source"] for chunk in context_chunks]))
            
            return {
                "answer": answer,
                "sources": sources,
                "context": context_chunks
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            raise


def main():
    """
    Example usage of the Azure RAG Backend.
    """
    try:
        # Initialize backend
        logger.info("Initializing Azure RAG Backend...")
        backend = AzureRAGBackend()
        
        # Create search index
        logger.info("Creating/updating search index...")
        backend.create_search_index()
        
        # Example: Ingest a document
        # Uncomment and modify with your document path
        # backend.ingest_document("path/to/meeting_minutes.pdf", "Q1_2024_Meeting")
        
        # Example: Query the system
        # result = backend.query("What were the key decisions made in the meeting?")
        # print(f"\nAnswer: {result['answer']}")
        # print(f"\nSources: {', '.join(result['sources'])}")
        
        logger.info("Azure RAG Backend initialized successfully!")
        logger.info("To use the backend:")
        logger.info("1. Set up your .env file with Azure credentials")
        logger.info("2. Ingest documents using: backend.ingest_document('path/to/file.pdf')")
        logger.info("3. Query using: backend.query('your question here')")
        
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        raise


if __name__ == "__main__":
    main()
