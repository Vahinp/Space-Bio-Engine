
import os, csv
from flask import Flask, jsonify
from flask_cors import CORS

CSV_PATH = os.getenv("CSV_PATH", "scraped_results.csv")
ORIGIN   = os.getenv("CORS_ORIGIN", "*")

def read_rows(csv_path):
    if not os.path.exists(csv_path):
        return []
    with open(csv_path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def build_year_counts(rows):
    counts = {}
    for r in rows:
        y = (r.get("year") or "").strip()
        if y.isdigit():
            counts[y] = counts.get(y, 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: int(kv[0])))

def create_app():
    app = Flask(__name__)
    CORS(app, resources={r"/api/*": {"origins": ORIGIN}})

    @app.get("/api/health")
    def health():
        rows = read_rows(CSV_PATH)
        return {"status": "ok", "csv": CSV_PATH, "count": len(rows)}

    @app.get("/api/papers")
    def papers():
        # return a small subset of fields if available
        rows = read_rows(CSV_PATH)
        out = []
        for r in rows:
            out.append({
                "id": r.get("id"),
                "title": r.get("title"),
                "url": r.get("url"),
                "date_iso": r.get("date_iso"),
                "year": r.get("year"),
                "abstract": r.get("abstract"),
                "source": r.get("source"),
                "doi": r.get("doi"),
            })
        return jsonify(out)

    @app.get("/api/stats/yearly")
    def stats_yearly():
        rows = read_rows(CSV_PATH)
        return jsonify({"counts": build_year_counts(rows)})

    return app

app = create_app()

if __name__ == "__main__":
    # Start server: http://127.0.0.1:5000
    app.run(host="127.0.0.1", port=5000, debug=True)
