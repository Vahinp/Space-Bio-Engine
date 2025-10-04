import os, csv
from flask import Flask, jsonify, request
from flask_cors import CORS

CSV_PATH = os.getenv("CSV_PATH", "data/papers.csv")
ORIGIN   = os.getenv("CORS_ORIGIN", "*")

def load_papers(csv_path: str):
    papers = []
    print(f"Looking for CSV at: {csv_path}")
    print(f"CSV exists: {os.path.exists(csv_path)}")
    if not os.path.exists(csv_path):
        # fallback sample so the app still runs
        print("Using fallback sample data")
        return [
            {"id": 1, "title": "Sample Space Biology Paper A", "url": "https://example.org/a"},
            {"id": 2, "title": "Microgravity Effects on Cells", "url": "https://example.org/b"},
        ]
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        print(f"CSV columns: {reader.fieldnames}")
        i = 1
        row_count = 0
        for row in reader:
            row_count += 1
            if row_count <= 3:  # Print first 3 rows for debugging
                print(f"Row {row_count}: {row}")
            
            # Handle different column name variations (including BOM)
            title = (row.get("title") or row.get("Title") or row.get("\ufeffTitle") or row.get("name") or "").strip()
            url   = (row.get("url") or row.get("Link") or row.get("link") or "").strip()
            # optional fields if present
            organism = (row.get("organism") or row.get("Organism") or "").strip()
            year     = (row.get("year") or row.get("Year") or "").strip()
            source   = (row.get("source") or row.get("Source") or "").strip()
            
            if row_count <= 3:
                print(f"  Parsed - title: '{title}', url: '{url}'")
            
            if title and url:
                papers.append({
                    "id": i, "title": title, "url": url,
                    "organism": organism or None,
                    "year": int(year) if year.isdigit() else None,
                    "source": source or None,
                })
                i += 1
            elif row_count <= 3:
                print(f"  SKIPPED - missing title or url")
        
        print(f"Total rows processed: {row_count}")
        print(f"Valid papers loaded: {len(papers)}")
    return papers

def create_app():
    app = Flask(__name__)
    CORS(app, resources={r"/api/*": {"origins": ORIGIN}})
    app.config["PAPERS"] = load_papers(CSV_PATH)

    @app.get("/api/health")
    def health():
        return {"status": "ok", "count": len(app.config["PAPERS"])}

    @app.get("/api/papers/titles")
    def titles():
        return jsonify([{"id": p["id"], "title": p["title"]} for p in app.config["PAPERS"]])

    @app.get("/api/papers")
    def list_papers():
        limit  = max(1, min(int(request.args.get("limit", 50)), 1000))
        offset = max(0, int(request.args.get("offset", 0)))
        data = app.config["PAPERS"][offset:offset+limit]
        return jsonify(data)

    @app.get("/api/papers/search")
    def search():
        q = (request.args.get("q") or "").strip().lower()
        if not q:
            return jsonify([])
        def matches(p):
            return q in p["title"].lower()
        results = [p for p in app.config["PAPERS"] if matches(p)]
        return jsonify(results[:50])

    return app

app = create_app()

if __name__ == "__main__":
    # Start server: http://127.0.0.1:5001
    app.run(host="127.0.0.1", port=5000, debug=True)
