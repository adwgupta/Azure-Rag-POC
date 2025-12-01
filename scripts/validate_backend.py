"""
Comprehensive validation script for Azure RAG backend setup.

This script checks:
1. Required environment variables are set
2. Azure OpenAI connectivity (embedding call)
3. Embedding vector dimension
4. Azure Search index metadata
5. Vector dimension matching between model and index

Run after activating your venv:
  python scripts/validate_backend.py
"""

import os
import sys
from dotenv import load_dotenv

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def check_env_vars():
    """Check that all required environment variables are set."""
    print_section("1. Checking Environment Variables")
    
    required_vars = [
        'AZURE_OPENAI_ENDPOINT',
        'AZURE_OPENAI_API_KEY',
        'AZURE_OPENAI_DEPLOYMENT_NAME',
        'AZURE_OPENAI_EMBEDDING_DEPLOYMENT',
        'AZURE_SEARCH_ENDPOINT',
        'AZURE_SEARCH_API_KEY',
        'AZURE_SEARCH_INDEX_NAME'
    ]
    
    load_dotenv()
    missing = []
    for var in required_vars:
        val = os.getenv(var)
        if val:
            # Hide secrets for security
            if 'KEY' in var:
                display = val[:10] + '...' if len(val) > 10 else '***'
            else:
                display = val
            print(f"  ✓ {var}: {display}")
        else:
            print(f"  ✗ {var}: MISSING")
            missing.append(var)
    
    if missing:
        print(f"\n  ERROR: Missing {len(missing)} required variables: {', '.join(missing)}")
        return False
    print("\n  All required variables found!")
    return True

def check_embedding_api():
    """Test Azure OpenAI embedding call and get vector dimension."""
    print_section("2. Testing Azure OpenAI Embedding API")
    
    try:
        from openai import AzureOpenAI
    except ImportError:
        print("  ERROR: openai module not installed. Run: pip install openai")
        return None
    
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    key = os.getenv("AZURE_OPENAI_API_KEY")
    emb_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")
    
    print(f"  Endpoint: {endpoint}")
    print(f"  Deployment: {emb_deployment}")
    print(f"  API Version: {api_version}")
    
    try:
        client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=key,
            api_version=api_version
        )
        print("  ✓ AzureOpenAI client created")
        
        print("  Calling embeddings.create()...")
        resp = client.embeddings.create(input="test", model=emb_deployment)
        vec = resp.data[0].embedding
        vec_dim = len(vec)
        print(f"  ✓ Embedding successful! Vector dimension: {vec_dim}")
        return vec_dim
    except Exception as e:
        print(f"  ✗ Embedding call failed: {e}")
        return None

def check_search_index(expected_vec_dim):
    """Check Azure Search index metadata."""
    print_section("3. Checking Azure AI Search Index")
    
    try:
        from azure.core.credentials import AzureKeyCredential
        from azure.search.documents.indexes import SearchIndexClient
    except ImportError:
        print("  ERROR: azure-search-documents module not installed. Run: pip install azure-search-documents")
        return False
    
    endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
    key = os.getenv("AZURE_SEARCH_API_KEY")
    index_name = os.getenv("AZURE_SEARCH_INDEX_NAME", "minutes-index")
    
    print(f"  Endpoint: {endpoint}")
    print(f"  Index name: {index_name}")
    
    try:
        client = SearchIndexClient(endpoint=endpoint, credential=AzureKeyCredential(key))
        print("  ✓ SearchIndexClient created")
        
        index = client.get_index(index_name)
        print(f"  ✓ Index '{index.name}' found")
        
        print("\n  Index fields:")
        for f in index.fields:
            vec_dim = getattr(f, 'vector_search_dimensions', None)
            if vec_dim:
                print(f"    - {f.name}: {f.type} (vector_dimensions={vec_dim})")
            else:
                print(f"    - {f.name}: {f.type}")
        
        # Check for embedding field and its dimension
        embedding_field = next((f for f in index.fields if f.name == 'embedding'), None)
        if not embedding_field:
            print("\n  ⚠ WARNING: 'embedding' field not found in index")
            return False
        
        index_vec_dim = getattr(embedding_field, 'vector_search_dimensions', None)
        if not index_vec_dim:
            print("\n  ⚠ WARNING: 'embedding' field has no vector_search_dimensions")
            return False
        
        print(f"\n  Index embedding vector dimension: {index_vec_dim}")
        if expected_vec_dim and expected_vec_dim != index_vec_dim:
            print(f"  ✗ MISMATCH: Model returns {expected_vec_dim}, index expects {index_vec_dim}")
            print(f"    FIX: Update AZURE_OPENAI_EMBEDDING_DEPLOYMENT or recreate the index with correct dimensions")
            return False
        
        print(f"  ✓ Vector dimensions match!")
        
        # Check vector search profiles
        if index.vector_search:
            profiles = [p.name for p in index.vector_search.profiles]
            print(f"  Vector search profiles: {profiles}")
        
        return True
    except Exception as e:
        print(f"  ✗ Search index check failed: {e}")
        return False

def check_backend_init():
    """Try to initialize the AzureRAGBackend."""
    print_section("4. Testing AzureRAGBackend Initialization")
    
    try:
        # Add backend folder to path
        sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))
        from backend import AzureRAGBackend
    except ImportError as e:
        print(f"  ✗ Could not import AzureRAGBackend: {e}")
        return False
    
    try:
        backend = AzureRAGBackend()
        print("  ✓ AzureRAGBackend initialized successfully")
        return True
    except Exception as e:
        print(f"  ✗ AzureRAGBackend initialization failed: {e}")
        return False

def main():
    """Run all validation checks."""
    print("\n" + "="*60)
    print("  Azure RAG Backend Validation")
    print("="*60)
    
    results = {
        'env': check_env_vars(),
        'embedding_dim': check_embedding_api(),
        'index': None,
        'backend': None
    }
    
    if results['env']:
        results['index'] = check_search_index(results['embedding_dim'])
    
    if results['index']:
        results['backend'] = check_backend_init()
    
    # Summary
    print_section("Summary")
    print(f"  Environment Variables: {'✓ PASS' if results['env'] else '✗ FAIL'}")
    print(f"  Azure OpenAI Embedding: {'✓ PASS' if results['embedding_dim'] else '✗ FAIL'}")
    print(f"  Azure Search Index: {'✓ PASS' if results['index'] else '✗ FAIL'}")
    print(f"  Backend Initialization: {'✓ PASS' if results['backend'] else '✗ FAIL'}")
    
    if all(results.values()):
        print("\n  ✓ All checks passed! Backend is ready.")
        print("  Next: Run 'python scripts/test_query_api.py' to test the query endpoint.")
        return 0
    else:
        print("\n  ✗ Some checks failed. See details above and fix the issues.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
