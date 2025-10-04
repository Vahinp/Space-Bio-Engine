# app.py
# -*- coding: utf-8 -*-
import os
import csv
from typing import List, Dict, Any

from flask import Flask, jsonify, request
from flask_cors import CORS

CSV_PATH = os.getenv("CSV_PATH", "papers.csv")
ORIGIN   = os.getenv("CORS_ORIGIN", "*")


def _safe_int(x, default=0):
    try:
        # handle "12", "12.0", 12, None
        return int(float(str(x)))
    except Exception:
        return default


def _safe_bool(x, default=False):
    if x is None:
        return default
    return str(x).strip().lower() in {"true", "1", "yes", "y"}


def save_papers(csv_path: str, papers: List[Dict[str, Any]]):
    """Save papers data to CSV file"""
    # Ensure directory exists (robust even if csv_path is just a filename)
    dirpath = os.path.dirname(os.path.abspath(csv_path))
    if dirpath and not os.path.exists(dirpath):
        os.makedirs(dirpath, exist_ok=True)

    # Define CSV columns
    fieldnames = [
        "id", "title", "url", "organism", "year", "source", "authors",
        "mission", "environment", "summary", "citations", "hasOSDR",
        "hasDOI", "bookmarked", "abstract", "keyResults", "methods",
        "conclusions", "doi", "osdrLink"
    ]

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for paper in papers:
            # Convert keyResults list to string for CSV storage
            row = dict(paper)  # shallow copy
            if isinstance(row.get("keyResults"), list):
                row["keyResults"] = "|".join(row["keyResults"])
            writer.writerow(row)

    print(f"Saved {len(papers)} papers to {csv_path}")


def load_papers(csv_path: str) -> List[Dict[str, Any]]:
    papers: List[Dict[str, Any]] = []
    print(f"Looking for CSV at: {csv_path}")
    print(f"CSV exists: {os.path.exists(csv_path)}")
    if not os.path.exists(csv_path):
        # fallback sample so the app still runs
        print("Using fallback sample data")
        return [
            {"id": "1", "title": "Sample Space Biology Paper A", "url": "https://example.org/a"},
            {"id": "2", "title": "Microgravity Effects on Cells", "url": "https://example.org/b"},
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
            url   = (row.get("url")   or row.get("Link")  or row.get("link")   or "").strip()
            # optional fields if present
            organism = (row.get("organism") or row.get("Organism") or "").strip()
            year_raw = (row.get("year") or row.get("Year") or "").strip()
            source   = (row.get("source") or row.get("Source") or "").strip()

            if row_count <= 3:
                print(f"  Parsed - title: '{title}', url: '{url}'")

            if title and url:
                # Parse keyResults from CSV (stored as pipe-separated string)
                key_results_str = (row.get("keyResults") or "").strip()
                key_results = key_results_str.split("|") if key_results_str else []

                papers.append({
                    "id": str(i),
                    "title": title,
                    "url": url,
                    "organism": organism or None,
                    "year": _safe_int(year_raw, default=2023) if year_raw else 2023,
                    "source": source or None,
                    "authors": (row.get("authors") or "Unknown Author"),
                    "mission": (row.get("mission") or "Unknown Mission"),
                    "environment": (row.get("environment") or "Space Environment"),
                    "summary": (row.get("summary") or (title[:100] + "..." if len(title) > 100 else title)),
                    "citations": _safe_int(row.get("citations", 0), default=0),
                    "hasOSDR": _safe_bool(row.get("hasOSDR"), default=False),
                    "hasDOI": _safe_bool(row.get("hasDOI"), default=False),
                    "bookmarked": _safe_bool(row.get("bookmarked"), default=False),
                    "abstract": (row.get("abstract") or title),
                    "keyResults": key_results,
                    "methods": (row.get("methods") or "Not specified"),
                    "conclusions": (row.get("conclusions") or "Not specified"),
                    "doi": (row.get("doi") or ""),
                    "osdrLink": (row.get("osdrLink") or "")
                })
                i += 1
            elif row_count <= 3:
                print("  SKIPPED - missing title or url")

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
        return jsonify([{"id": p.get("id"), "title": p.get("title")} for p in app.config["PAPERS"]])

    @app.get("/api/papers")
    def list_papers():
        try:
            limit  = max(1, min(int(request.args.get("limit", 50)), 1000))
            offset = max(0, int(request.args.get("offset", 0)))
        except Exception:
            limit, offset = 50, 0
        data = app.config["PAPERS"][offset:offset+limit]
        return jsonify(data)

    @app.get("/api/papers/search")
    def search():
        q = (request.args.get("q") or "").strip().lower()
        if not q:
            return jsonify([])
        def matches(p):
            t = (p.get("title") or "").lower()
            return q in t
        results = [p for p in app.config["PAPERS"] if matches(p)]
        return jsonify(results[:50])

    @app.post("/api/papers")
    def create_paper():
        """Create a new paper"""
        try:
            data = request.get_json(force=True, silent=True) or {}
            if not data.get("title") or not data.get("url"):
                return jsonify({"error": "Title and URL are required"}), 400

            # Generate new ID
            existing_ids = [int(p.get("id", 0)) for p in app.config["PAPERS"] if str(p.get("id", "")).isdigit()]
            max_id = max(existing_ids, default=0)
            new_id = str(max_id + 1)

            # Create new paper with defaults
            title = data["title"]
            new_paper = {
                "id": new_id,
                "title": title,
                "url": data["url"],
                "organism": data.get("organism"),
                "year": _safe_int(data.get("year", 2023), default=2023),
                "source": data.get("source"),
                "authors": data.get("authors", "Unknown Author"),
                "mission": data.get("mission", "Unknown Mission"),
                "environment": data.get("environment", "Space Environment"),
                "summary": data.get("summary", title[:100] + "..." if len(title) > 100 else title),
                "citations": _safe_int(data.get("citations", 0), default=0),
                "hasOSDR": _safe_bool(data.get("hasOSDR"), default=False),
                "hasDOI": _safe_bool(data.get("hasDOI"), default=False),
                "bookmarked": _safe_bool(data.get("bookmarked"), default=False),
                "abstract": data.get("abstract", title),
                "keyResults": data.get("keyResults", []),
                "methods": data.get("methods", "Not specified"),
                "conclusions": data.get("conclusions", "Not specified"),
                "doi": data.get("doi", ""),
                "osdrLink": data.get("osdrLink", "")
            }

            # Add to papers list
            app.config["PAPERS"].append(new_paper)

            # Save to CSV
            save_papers(CSV_PATH, app.config["PAPERS"])

            return jsonify(new_paper), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.put("/api/papers/<paper_id>")
    def update_paper(paper_id):
        """Update an existing paper"""
        try:
            data = request.get_json(force=True, silent=True) or {}

            # Find the paper
            paper = next((p for p in app.config["PAPERS"] if p.get("id") == paper_id), None)
            if not paper:
                return jsonify({"error": "Paper not found"}), 404

            # Update fields (don't allow ID changes)
            for key, value in data.items():
                if key != "id":
                    paper[key] = value

            # Save to CSV
            save_papers(CSV_PATH, app.config["PAPERS"])

            return jsonify(paper)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.delete("/api/papers/<paper_id>")
    def delete_paper(paper_id):
        """Delete a paper"""
        try:
            before = len(app.config["PAPERS"])
            app.config["PAPERS"] = [p for p in app.config["PAPERS"] if p.get("id") != paper_id]
            after = len(app.config["PAPERS"])

            if after == before:
                return jsonify({"error": "Paper not found"}), 404

            # Save to CSV
            save_papers(CSV_PATH, app.config["PAPERS"])

            return jsonify({"message": "Paper deleted successfully"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.post("/api/papers/bulk")
    def bulk_save_papers():
        """Save multiple papers at once (useful for scraped data)"""
        try:
            data = request.get_json(force=True, silent=True)
            if not isinstance(data, list):
                return jsonify({"error": "Expected array of papers"}), 400

            existing_ids = [int(p.get("id", 0)) for p in app.config["PAPERS"] if str(p.get("id", "")).isdigit()]
            base_id = max(existing_ids, default=0)
            new_papers = []

            for i, paper_data in enumerate(data):
                if not paper_data.get("title") or not paper_data.get("url"):
                    continue  # Skip invalid papers

                title = paper_data["title"]
                new_id = str(base_id + i + 1)
                new_paper = {
                    "id": new_id,
                    "title": title,
                    "url": paper_data["url"],
                    "organism": paper_data.get("organism"),
                    "year": _safe_int(paper_data.get("year", 2023), default=2023),
                    "source": paper_data.get("source"),
                    "authors": paper_data.get("authors", "Unknown Author"),
                    "mission": paper_data.get("mission", "Unknown Mission"),
                    "environment": paper_data.get("environment", "Space Environment"),
                    "summary": paper_data.get("summary", title[:100] + "..." if len(title) > 100 else title),
                    "citations": _safe_int(paper_data.get("citations", 0), default=0),
                    "hasOSDR": _safe_bool(paper_data.get("hasOSDR"), default=False),
                    "hasDOI": _safe_bool(paper_data.get("hasDOI"), default=False),
                    "bookmarked": _safe_bool(paper_data.get("bookmarked"), default=False),
                    "abstract": paper_data.get("abstract", title),
                    "keyResults": paper_data.get("keyResults", []),
                    "methods": paper_data.get("methods", "Not specified"),
                    "conclusions": paper_data.get("conclusions", "Not specified"),
                    "doi": paper_data.get("doi", ""),
                    "osdrLink": paper_data.get("osdrLink", "")
                }
                new_papers.append(new_paper)

            # Add all new papers
            app.config["PAPERS"].extend(new_papers)

            # Save to CSV
            save_papers(CSV_PATH, app.config["PAPERS"])

            return jsonify({
                "message": f"Successfully saved {len(new_papers)} papers",
                "saved_count": len(new_papers),
                "total_papers": len(app.config["PAPERS"])
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return app


app = create_app()

if __name__ == "__main__":
    # Start server: http://127.0.0.1:5000
    app.run(host="127.0.0.1", port=5000, debug=True)
