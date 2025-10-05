# BioSpace Explorer

Quick start for frontend and backend.

## Frontend (Next.js)

1. In the project root run:
```bash
npm install
npm run dev
```
App: http://localhost:3000

## Backend (Flask + Elasticsearch)

1. In a new terminal run:
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app_elasticsearch.py
```
API: http://127.0.0.1:5003

Notes:
- Put your keys in backend/.env (e.g., GEMINI_API_KEY, ES_ENDPOINT).
- Ensure Elasticsearch is up and reachable by ES_ENDPOINT.
