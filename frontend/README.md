Azure RAG POC — Frontend

This folder contains a tiny static frontend that talks to the Python FastAPI server in the repo.

Files:
- index.html — main page
- app.js — JS to call the API endpoints (/health, /create-index, /ingest, /query)
- styles.css — small styles

How to use:
1. Start the backend API server (in the repo root):

   python api_server.py

   By default the server listens at http://localhost:8000

2. Open `frontend/index.html` in your browser. For local development, you can also run a small HTTP server from the `frontend` directory (recommended) such as:

   # Using Python 3 (PowerShell)
   cd frontend; python -m http.server 8080; # then open http://localhost:8080

3. Configure the API base URL at the top of the UI if your API uses a different host/port.

Notes and hints:
- CORS is enabled in `api_server.py` for all origins to simplify local development. For production restrict allowed origins.
- The ingest flow uploads the selected file using a multipart form to `/ingest`.
- Query sends JSON to `/query` and will render the answer with cited sources and retrieved chunks.
- If you use HTTPS or a reverse proxy, update the API Base URL accordingly.

Next steps (optional):
- Replace the static UI with a React/Vite app if you want a richer developer experience.
- Add authentication on the API server and wire the frontend to use tokens.
