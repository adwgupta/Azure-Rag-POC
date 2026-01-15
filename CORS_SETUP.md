# CORS Configuration Fix - Running the Backend

## What Was Changed

CORS (Cross-Origin Resource Sharing) middleware has been configured to allow requests from your frontend to the backend API. The changes ensure that preflight requests (OPTIONS) are properly handled.

### Changes Made:

1. **main.py**: Moved CORS middleware to be added immediately after app initialization (before routes)
2. **api_server.py**: Updated CORS configuration to explicitly include OPTIONS method
3. **Created run_backend.py**: A startup script for easy backend execution

## How to Run the Backend

### Option 1: Using the New Startup Script (Recommended)

```bash
cd /path/to/Azure-Rag-POC
python run_backend.py
```

This will start the server at `http://127.0.0.1:8000` with proper CORS headers.

### Option 2: Using Uvicorn Directly

```bash
cd /path/to/Azure-Rag-POC
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

### Option 3: Running via API Server Module

```bash
cd /path/to/Azure-Rag-POC/backend
python api_server.py
```

## Verifying CORS is Working

Once your backend is running, you can verify CORS is configured correctly by checking the response headers:

```bash
curl -i -X OPTIONS http://127.0.0.1:8000/chat \
  -H "Origin: http://127.0.0.1:5500" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type"
```

You should see these headers in the response:
```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: *
```

## Frontend Configuration

Your frontend is correctly configured to make requests to:
- **API Base URL**: http://127.0.0.1:8000 (set in index.html)
- **Frontend Server**: http://127.0.0.1:5500

These are different origins, which is why CORS is necessary.

## Testing the Chat Endpoint

Once both servers are running:

1. **Backend**: `python run_backend.py` (or your preferred method)
2. **Frontend**: Serve the frontend folder on port 5500
   ```bash
   cd frontend
   python -m http.server 5500
   ```

3. Open `http://127.0.0.1:5500` in your browser
4. Try the chat functionality - it should now work without CORS errors

## CORS Configuration Details

The CORS middleware is now configured with:
- **allow_origins**: `["*"]` - Allows requests from any origin (you may want to restrict this in production)
- **allow_credentials**: `True` - Allows credentials in requests
- **allow_methods**: `["GET", "POST", "PUT", "DELETE", "OPTIONS"]` - Explicitly includes OPTIONS for preflight requests
- **allow_headers**: `["*"]` - Allows any headers

## Production Considerations

For production deployment, consider changing:
```python
allow_origins=["https://yourdomain.com"]  # Instead of "*"
```

This is more secure than allowing all origins.
