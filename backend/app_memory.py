import os, csv
from flask import Flask, jsonify, request
from flask_cors import CORS
from pmc_scrape import parse_pmc_article, batch_parse_pmc_articles
import time

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
                    "id": str(i), "title": title, "url": url,
                    "organism": organism or None,
                    "year": int(year) if year.isdigit() else 2023,
                    "source": source or None,
                    "authors": "Unknown Author",
                    "mission": "Unknown Mission",
                    "environment": "Space Environment",
                    "summary": title[:100] + "..." if len(title) > 100 else title,
                    "citations": 0,
                    "hasOSDR": False,
                    "hasDOI": False,
                    "bookmarked": False,
                    "abstract": title,
                    "keyResults": [],
                    "methods": "Not specified",
                    "conclusions": "Not specified",
                    "doi": "",
                    "osdrLink": ""
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

    @app.post("/api/pmc/parse")
    def parse_pmc_endpoint():
        """Parse a single PMC article and optionally add it to the papers list."""
        try:
            data = request.get_json(force=True) or {}
            url = (data.get("url") or "").strip()
            if not url:
                return {"error": "url is required"}, 400
            
            print(f"Parsing PMC article: {url}")
            result = parse_pmc_article(url)
            
            # If parsing was successful and user wants to add to papers list
            if data.get("add_to_papers", False) and not result.get("error"):
                # Convert PMC result to our paper format
                new_paper = {
                    "id": str(len(app.config["PAPERS"]) + 1),
                    "title": result.get("title") or "Untitled PMC Article",
                    "url": result.get("html_url") or url,
                    "organism": "Unknown",
                    "year": result.get("year", 2023),
                    "source": result.get("source", "PMC"),
                    "authors": result.get("authors", "Unknown Author"),
                    "mission": "Unknown Mission",
                    "environment": "Space Environment",
                    "summary": result.get("abstract", "")[:200] + "..." if result.get("abstract") and len(result.get("abstract", "")) > 200 else result.get("abstract", ""),
                    "citations": 0,
                    "hasOSDR": False,
                    "hasDOI": bool(result.get("doi")),
                    "bookmarked": False,
                    "abstract": result.get("abstract", ""),
                    "keyResults": [],
                    "methods": "Not specified",
                    "conclusions": "Not specified",
                    "doi": result.get("doi", ""),
                    "osdrLink": "",
                    "taskBookLink": result.get("pdf_url", "")
                }
                
                app.config["PAPERS"].append(new_paper)
                print(f"Added new paper to list. Total papers: {len(app.config['PAPERS'])}")
            
            return jsonify(result)
            
        except Exception as e:
            print(f"Error in PMC parse endpoint: {str(e)}")
            return {"error": str(e)}, 500

    @app.post("/api/pmc/batch-parse")
    def batch_parse_pmc_endpoint():
        """Parse multiple PMC articles in batch."""
        try:
            data = request.get_json(force=True) or {}
            urls = data.get("urls", [])
            delay = data.get("delay", 1.0)
            add_to_papers = data.get("add_to_papers", False)
            
            if not urls:
                return {"error": "urls array is required"}, 400
            
            print(f"Batch parsing {len(urls)} PMC articles")
            results = batch_parse_pmc_articles(urls, delay)
            
            # If user wants to add all successful results to papers list
            if add_to_papers:
                added_count = 0
                for result in results:
                    if not result.get("error") and result.get("title"):
                        new_paper = {
                            "id": str(len(app.config["PAPERS"]) + 1),
                            "title": result.get("title", "Untitled PMC Article"),
                            "url": result.get("html_url", ""),
                            "organism": "Unknown",
                            "year": result.get("year", 2023),
                            "source": result.get("source", "PMC"),
                            "authors": result.get("authors", "Unknown Author"),
                            "mission": "Unknown Mission",
                            "environment": "Space Environment",
                            "summary": result.get("abstract", "")[:200] + "..." if result.get("abstract") and len(result.get("abstract", "")) > 200 else result.get("abstract", ""),
                            "citations": 0,
                            "hasOSDR": False,
                            "hasDOI": bool(result.get("doi")),
                            "bookmarked": False,
                            "abstract": result.get("abstract", ""),
                            "keyResults": [],
                            "methods": "Not specified",
                            "conclusions": "Not specified",
                            "doi": result.get("doi", ""),
                            "osdrLink": "",
                            "taskBookLink": result.get("pdf_url", "")
                        }
                        app.config["PAPERS"].append(new_paper)
                        added_count += 1
                
                print(f"Added {added_count} new papers to list. Total papers: {len(app.config['PAPERS'])}")
            
            return jsonify({
                "results": results,
                "total_parsed": len(results),
                "successful": len([r for r in results if not r.get("error")]),
                "added_to_papers": added_count if add_to_papers else 0
            })
            
        except Exception as e:
            print(f"Error in batch PMC parse endpoint: {str(e)}")
            return {"error": str(e)}, 500

    @app.post("/api/papers/enrich-all")
    def enrich_all_papers():
        """Parse and enrich all PMC articles currently in memory."""
        try:
            papers = app.config["PAPERS"]
            print(f"Starting to enrich {len(papers)} papers...")
            
            enriched_count = 0
            error_count = 0
            results = []
            
            for i, paper in enumerate(papers):
                url = paper.get("url", "")
                
                # Check if it's a PMC URL and hasn't been enriched yet
                # A paper is considered enriched if it has a real abstract (not just the title) and real authors
                is_enriched = (
                    paper.get("abstract") and 
                    len(paper.get("abstract", "")) > 100 and  # Real abstract should be longer
                    paper.get("authors") and 
                    paper.get("authors") != "Unknown Author"
                )
                
                if ('pmc.ncbi.nlm.nih.gov' in url or 'ncbi.nlm.nih.gov/pmc' in url) and not is_enriched:
                    print(f"Enriching paper {i+1}/{len(papers)}: {paper.get('title', 'Unknown')[:50]}...")
                    
                    try:
                        # Parse the PMC article
                        result = parse_pmc_article(url)
                        
                        if result.get('error'):
                            print(f"  ❌ Error: {result.get('error')}")
                            error_count += 1
                            results.append({
                                "id": paper.get("id"),
                                "title": paper.get("title"),
                                "status": "error",
                                "error": result.get('error')
                            })
                        else:
                            # Update the paper with enriched data
                            paper["title"] = result.get("title", paper.get("title", ""))
                            paper["authors"] = result.get("authors", "Unknown Author")
                            paper["year"] = result.get("year", 2023)
                            paper["doi"] = result.get("doi", "")
                            paper["abstract"] = result.get("abstract", "")
                            paper["pdf_url"] = result.get("pdf_url", "")
                            paper["pmcid"] = result.get("pmcid", "")
                            paper["source"] = "PMC"
                            paper["hasDOI"] = bool(result.get("doi"))
                            paper["taskBookLink"] = result.get("pdf_url", "")
                            
                            # Update summary with abstract if available
                            if result.get("abstract"):
                                abstract = result.get("abstract", "")
                                paper["summary"] = abstract[:200] + "..." if len(abstract) > 200 else abstract
                            
                            print(f"  ✅ Enriched: {result.get('title', 'Unknown')[:50]}...")
                            print(f"     Authors: {result.get('authors', 'Unknown')}")
                            print(f"     Year: {result.get('year', 'Unknown')}")
                            print(f"     Abstract: {len(result.get('abstract', ''))} chars")
                            
                            enriched_count += 1
                            results.append({
                                "id": paper.get("id"),
                                "title": paper.get("title"),
                                "status": "success",
                                "authors": result.get("authors"),
                                "year": result.get("year"),
                                "abstract_length": len(result.get("abstract", ""))
                            })
                    
                    except Exception as e:
                        print(f"  ❌ Exception: {str(e)}")
                        error_count += 1
                        results.append({
                            "id": paper.get("id"),
                            "title": paper.get("title"),
                            "status": "error",
                            "error": str(e)
                        })
                    
                    # Small delay to be respectful
                    time.sleep(0.5)
                else:
                    # Skip non-PMC URLs or already enriched papers
                    results.append({
                        "id": paper.get("id"),
                        "title": paper.get("title"),
                        "status": "skipped",
                        "reason": "Not PMC URL" if not ('pmc.ncbi.nlm.nih.gov' in url or 'ncbi.nlm.nih.gov/pmc' in url) else "Already enriched"
                    })
            
            print(f"Enrichment complete! Enriched: {enriched_count}, Errors: {error_count}")
            
            return jsonify({
                "success": True,
                "total_papers": len(papers),
                "enriched_count": enriched_count,
                "error_count": error_count,
                "skipped_count": len(papers) - enriched_count - error_count,
                "results": results
            })
            
        except Exception as e:
            print(f"Error in enrich all papers endpoint: {str(e)}")
            return {"error": str(e)}, 500

    return app

app = create_app()

if __name__ == "__main__":
    # Start server: http://127.0.0.1:5001
    app.run(host="127.0.0.1", port=5000, debug=True)
