"""
Example Usage Script for Azure RAG Backend

This script demonstrates how to use the Azure RAG backend for processing
and querying meeting minutes.

Make sure to:
1. Set up your .env file with Azure credentials
2. Have some sample documents ready to test
"""

import logging
from azure_rag_backend import AzureRAGBackend

# Setup logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def example_basic_usage():
    """
    Basic example: Initialize, create index, ingest document, and query.
    """
    print("\n" + "="*60)
    print("BASIC USAGE EXAMPLE")
    print("="*60 + "\n")
    
    try:
        # Step 1: Initialize the backend
        print("1. Initializing Azure RAG Backend...")
        backend = AzureRAGBackend()
        print("   ✓ Backend initialized successfully\n")
        
        # Step 2: Create the search index
        print("2. Creating search index...")
        backend.create_search_index()
        print("   ✓ Search index created/updated\n")
        
        # Step 3: Ingest a document (replace with your document path)
        print("3. Ingesting a document...")
        print("   NOTE: Replace 'path/to/your/document.pdf' with actual file path")
        
        # Uncomment and modify the following lines to ingest your document:
        # result = backend.ingest_document(
        #     file_path="path/to/your/meeting_minutes.pdf",
        #     source_name="Q1_2024_Board_Meeting"
        # )
        # print(f"   ✓ Ingested {result['chunks_processed']} chunks from {result['source']}\n")
        
        # Step 4: Query the system
        print("4. Querying the system...")
        print("   NOTE: This will only work after you've ingested documents")
        
        # Uncomment the following lines to query after ingesting documents:
        # response = backend.query(
        #     question="What were the main topics discussed in the meeting?",
        #     top_k=5
        # )
        # print(f"\n   Question: What were the main topics discussed in the meeting?")
        # print(f"\n   Answer:\n   {response['answer']}\n")
        # print(f"   Sources: {', '.join(response['sources'])}\n")
        
        print("\n✓ Example completed successfully!")
        print("\nNext steps:")
        print("1. Uncomment the ingest_document line and provide your document path")
        print("2. Uncomment the query line to ask questions")
        print("3. Run this script again to see it in action")
        
    except Exception as e:
        logger.error(f"Error in example: {str(e)}")
        print(f"\n✗ Error: {str(e)}")
        print("\nMake sure you have:")
        print("1. Created a .env file with your Azure credentials")
        print("2. Set up Azure OpenAI and Azure AI Search services")


def example_multiple_documents():
    """
    Example: Ingest multiple documents and query across all of them.
    """
    print("\n" + "="*60)
    print("MULTIPLE DOCUMENTS EXAMPLE")
    print("="*60 + "\n")
    
    try:
        backend = AzureRAGBackend()
        
        # List of documents to ingest
        documents = [
            # Add your document paths here
            # ("path/to/document1.pdf", "Meeting_Jan_2024"),
            # ("path/to/document2.docx", "Meeting_Feb_2024"),
            # ("path/to/document3.txt", "Meeting_Mar_2024"),
        ]
        
        if not documents:
            print("NOTE: Add document paths to the 'documents' list to test this example")
            return
        
        print(f"Ingesting {len(documents)} documents...\n")
        
        for file_path, source_name in documents:
            print(f"Processing: {source_name}")
            result = backend.ingest_document(file_path, source_name)
            print(f"  ✓ Ingested {result['chunks_processed']} chunks\n")
        
        # Query across all documents
        questions = [
            "What are the common themes across all meetings?",
            "What decisions were made?",
            "Who were the key participants?",
        ]
        
        print("\nQuerying across all documents:\n")
        for question in questions:
            response = backend.query(question, top_k=10)
            print(f"Q: {question}")
            print(f"A: {response['answer']}\n")
            print(f"   Sources: {', '.join(response['sources'])}\n")
            print("-" * 60 + "\n")
        
    except Exception as e:
        logger.error(f"Error in example: {str(e)}")


def example_search_only():
    """
    Example: Search for similar content without generating answers.
    """
    print("\n" + "="*60)
    print("SEARCH ONLY EXAMPLE")
    print("="*60 + "\n")
    
    try:
        backend = AzureRAGBackend()
        
        # Search for similar chunks
        query = "budget allocation"
        print(f"Searching for: '{query}'\n")
        
        results = backend.search_similar(query, top_k=3)
        
        print(f"Found {len(results)} similar chunks:\n")
        for i, result in enumerate(results, 1):
            print(f"{i}. Source: {result['source']}, Chunk: {result['chunk_id']}")
            print(f"   Score: {result['score']:.4f}")
            print(f"   Content: {result['content'][:200]}...")
            print()
        
    except Exception as e:
        logger.error(f"Error in example: {str(e)}")


def main():
    """
    Main function to run examples.
    """
    print("\n" + "="*60)
    print("AZURE RAG BACKEND - EXAMPLE USAGE")
    print("="*60)
    
    # Run basic example
    example_basic_usage()
    
    # Uncomment to run additional examples:
    # example_multiple_documents()
    # example_search_only()
    
    print("\n" + "="*60)
    print("For more information, see README.md")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
