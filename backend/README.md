# Space Bio Engine - Backend API

A simple Flask API that loads papers from CSV and provides search/filtering endpoints.

## Quick Start

```bash
# 1. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set environment variables (optional)
export CSV_PATH=data/papers.csv
export CORS_ORIGIN=http://localhost:5173

# 4. Run the server
python app_memory.py
```

Server will start at: http://127.0.0.1:5001

## API Endpoints

- `GET /api/health` - Health check
- `GET /api/papers/titles` - List all paper titles
- `GET /api/papers?limit=50&offset=0` - Paginated papers list
- `GET /api/papers/search?q=query` - Search papers by title

## Quick Test

```bash
# Health check
curl -s http://127.0.0.1:5001/api/health

# List titles
curl -s http://127.0.0.1:5001/api/papers/titles

# Search
curl -s 'http://127.0.0.1:5001/api/papers/search?q=microgravity'
```

## CSV Format

The CSV file should have headers: `title,url,organism,year,source`

Example:
```csv
title,url,organism,year,source
"Sample Paper","https://example.org","Mouse",2023,"PubMed"
```

If no CSV is found, the app will use sample data.
