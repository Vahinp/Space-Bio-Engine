#!/usr/bin/env python3
"""
Flask API for Space Bio Engine with SQLite database backend
"""

import os
import sqlite3
from flask import Flask, jsonify, request
from flask_cors import CORS
from pmc_scrape import parse_pmc_article, batch_parse_pmc_articles
from database import (
    create_database, migrate_csv_to_database, get_papers, search_papers, 
    get_papers_count, get_pmc_papers_to_enrich, update_paper_enrichment
)
import time
import json

ORIGIN = os.getenv("CORS_ORIGIN", "*")

def create_app():
    app = Flask(__name__)
    CORS(app, resources={r"/api/*": {"origins": ORIGIN}})
    
    # Initialize database on startup
    print("🗄️ Initializing database...")
    create_database()
    
    # Check if we need to migrate CSV data
    if get_papers_count() == 0:
        print("📄 Migrating CSV data to database...")
        migrate_csv_to_database("data/papers.csv")
    
    print(f"✅ Database ready with {get_papers_count()} papers")

    @app.get("/api/health")
    def health():
        return {"status": "ok", "count": get_papers_count()}

    @app.get("/api/papers/titles")
    def titles():
        papers = get_papers(limit=1000)  # Get all papers for titles
        return jsonify([{"id": p["id"], "title": p["title"]} for p in papers])

    @app.get("/api/papers")
    def list_papers():
        limit = max(1, min(int(request.args.get("limit", 50)), 1000))
        offset = max(0, int(request.args.get("offset", 0)))
        
        papers = get_papers(limit=limit, offset=offset)
        
        # Convert database rows to API format
        api_papers = []
        for paper in papers:
            # Parse keyResults JSON string
            key_results = []
            if paper.get("keyResults"):
                try:
                    key_results = json.loads(paper["keyResults"])
                except json.JSONDecodeError:
                    key_results = []
            
            api_paper = {
                "id": str(paper["id"]),
                "title": paper["title"],
                "url": paper["url"],
                "organism": paper["organism"],
                "year": paper["year"],
                "source": paper["source"],
                "authors": paper["authors"],
                "mission": paper["mission"],
                "environment": paper["environment"],
                "summary": paper["summary"],
                "citations": paper["citations"],
                "hasOSDR": bool(paper["hasOSDR"]),
                "hasDOI": bool(paper["hasDOI"]),
                "bookmarked": bool(paper["bookmarked"]),
                "abstract": paper["abstract"],
                "keyResults": key_results,
                "methods": paper["methods"],
                "conclusions": paper["conclusions"],
                "doi": paper["doi"],
                "osdrLink": paper["osdrLink"],
                "taskBookLink": paper["taskBookLink"]
            }
            api_papers.append(api_paper)
        
        return jsonify(api_papers)

    @app.get("/api/papers/search")
    def search():
        query = (request.args.get("q") or "").strip()
        if not query:
            return jsonify([])
        
        papers = search_papers(query, limit=50)
        
        # Convert to API format (same as list_papers)
        api_papers = []
        for paper in papers:
            key_results = []
            if paper.get("keyResults"):
                try:
                    key_results = json.loads(paper["keyResults"])
                except json.JSONDecodeError:
                    key_results = []
            
            api_paper = {
                "id": str(paper["id"]),
                "title": paper["title"],
                "url": paper["url"],
                "organism": paper["organism"],
                "year": paper["year"],
                "source": paper["source"],
                "authors": paper["authors"],
                "mission": paper["mission"],
                "environment": paper["environment"],
                "summary": paper["summary"],
                "citations": paper["citations"],
                "hasOSDR": bool(paper["hasOSDR"]),
                "hasDOI": bool(paper["hasDOI"]),
                "bookmarked": bool(paper["bookmarked"]),
                "abstract": paper["abstract"],
                "keyResults": key_results,
                "methods": paper["methods"],
                "conclusions": paper["conclusions"],
                "doi": paper["doi"],
                "osdrLink": paper["osdrLink"],
                "taskBookLink": paper["taskBookLink"]
            }
            api_papers.append(api_paper)
        
        return jsonify(api_papers)

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
                # Convert PMC result to our paper format and add to database
                # This would require a new function to add papers to database
                print(f"Adding new paper to database: {result.get('title', 'Unknown')}")
                # TODO: Implement add_paper_to_database function
                
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
                # TODO: Implement batch add to database
                print(f"Would add {len([r for r in results if not r.get('error')])} papers to database")
            
            return jsonify({
                "results": results,
                "total_parsed": len(results),
                "successful": len([r for r in results if not r.get("error")]),
                "added_to_papers": 0  # TODO: Update when batch add is implemented
            })
            
        except Exception as e:
            print(f"Error in batch PMC parse endpoint: {str(e)}")
            return {"error": str(e)}, 500

        @app.post("/api/papers/add")
        def add_paper():
            """Add a new paper by parsing its URL and storing in database."""
            try:
                data = request.get_json(force=True) or {}
                url = (data.get("url") or "").strip()
                
                if not url:
                    return {"error": "URL is required"}, 400
                
                print(f"Adding new paper from URL: {url}")
                
                # Parse the article
                result = parse_pmc_article(url)
                
                if result.get('error'):
                    return {"error": f"Failed to parse article: {result.get('error')}"}, 400
                
                # Generate new ID
                existing_papers = get_all_papers_from_db(DATABASE_PATH)
                new_id = str(len(existing_papers) + 1)
                
                # Create paper data
                paper_data = {
                    "id": new_id,
                    "title": result.get("title", "Untitled Article"),
                    "url": result.get("html_url", url),
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
                    "keyResults": "[]",
                    "methods": "Not specified",
                    "conclusions": "Not specified",
                    "doi": result.get("doi", ""),
                    "osdrLink": "",
                    "taskBookLink": result.get("pdf_url", "")
                }
                
                # Insert into database
                conn = sqlite3.connect(DATABASE_PATH)
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO papers (id, title, url, organism, year, source, authors, mission, environment, summary, citations, hasOSDR, hasDOI, bookmarked, abstract, keyResults, methods, conclusions, doi, osdrLink, taskBookLink)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    paper_data["id"], paper_data["title"], paper_data["url"], paper_data["organism"], 
                    paper_data["year"], paper_data["source"], paper_data["authors"], paper_data["mission"], 
                    paper_data["environment"], paper_data["summary"], paper_data["citations"], 
                    paper_data["hasOSDR"], paper_data["hasDOI"], paper_data["bookmarked"], 
                    paper_data["abstract"], paper_data["keyResults"], paper_data["methods"], 
                    paper_data["conclusions"], paper_data["doi"], paper_data["osdrLink"], 
                    paper_data["taskBookLink"]
                ))
                conn.commit()
                conn.close()
                
                print(f"✅ Successfully added paper: {result.get('title', 'Unknown')[:50]}...")
                
                return jsonify({
                    "success": True,
                    "message": "Paper added successfully",
                    "paper": paper_data
                })
                
            except Exception as e:
                print(f"Error adding paper: {str(e)}")
                return {"error": str(e)}, 500

        @app.post("/api/papers/enrich-all")
        def enrich_all_papers():
            """Parse and enrich all PMC articles currently in database."""
            try:
                # Get papers that need enrichment
                papers_to_enrich = get_pmc_papers_to_enrich()
                print(f"Starting to enrich {len(papers_to_enrich)} papers...")
                
                enriched_count = 0
                error_count = 0
                results = []
                
                for i, paper in enumerate(papers_to_enrich):
                    url = paper.get("url", "")
                    paper_id = paper.get("id")
                    
                    print(f"Enriching paper {i+1}/{len(papers_to_enrich)}: {paper.get('title', 'Unknown')[:50]}...")
                    
                    try:
                        # Parse the PMC article
                        result = parse_pmc_article(url)
                        
                        if result.get('error'):
                            print(f"  ❌ Error: {result.get('error')}")
                            error_count += 1
                            results.append({
                                "id": str(paper_id),
                                "title": paper.get("title"),
                                "status": "error",
                                "error": result.get('error')
                            })
                        else:
                            # Update the paper in database with enriched data
                            update_paper_enrichment(paper_id, result)
                            
                            print(f"  ✅ Enriched: {result.get('title', 'Unknown')[:50]}...")
                            print(f"     Authors: {result.get('authors', 'Unknown')}")
                            print(f"     Year: {result.get('year', 'Unknown')}")
                            print(f"     Abstract: {len(result.get('abstract', ''))} chars")
                            
                            enriched_count += 1
                            results.append({
                                "id": str(paper_id),
                                "title": result.get("title", paper.get("title")),
                                "status": "success",
                                "authors": result.get("authors"),
                                "year": result.get("year"),
                                "abstract_length": len(result.get("abstract", ""))
                            })
                    
                    except Exception as e:
                        print(f"  ❌ Exception: {str(e)}")
                        error_count += 1
                        results.append({
                            "id": str(paper_id),
                            "title": paper.get("title"),
                            "status": "error",
                            "error": str(e)
                        })
                    
                    # Small delay to be respectful
                    time.sleep(0.5)
                
                print(f"Enrichment complete! Enriched: {enriched_count}, Errors: {error_count}")
                
                return jsonify({
                    "success": True,
                    "total_papers": len(papers_to_enrich),
                    "enriched_count": enriched_count,
                    "error_count": error_count,
                    "skipped_count": 0,  # All papers in the list needed enrichment
                    "results": results
                })
                
            except Exception as e:
                print(f"Error in enrich all papers endpoint: {str(e)}")
                return {"error": str(e)}, 500

    return app

if __name__ == "__main__":
    app = create_app()
    # Start server: http://127.0.0.1:5000
    app.run(host="127.0.0.1", port=5000, debug=True)
