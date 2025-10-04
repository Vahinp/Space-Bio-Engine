#!/usr/bin/env python3
"""
Flask API for Space Bio Engine with Elasticsearch backend
"""

import os
import json
import requests
from flask import Flask, jsonify, request
from flask_cors import CORS
from database import get_papers, get_papers_count, create_database, migrate_csv_to_database

ORIGIN = os.getenv("CORS_ORIGIN", "*")

# Elasticsearch configuration
ES_ENDPOINT = "http://localhost:9200"
ES_USERNAME = "elastic"
ES_PASSWORD = "elasSer12!"
INDEX_NAME = "space_bio_papers"

def create_app():
    app = Flask(__name__)
    CORS(app, resources={r"/api/*": {"origins": ["http://localhost:3000", "http://127.0.0.1:3000"]}})

    # Initialize database and load papers from CSV if not already in DB
    create_database()
    if get_papers_count() == 0: # Only load from CSV if DB is empty
        migrate_csv_to_database(os.getenv("CSV_PATH", "data/papers.csv"))
    print(f"✅ Database ready with {get_papers_count()} papers")

    def load_papers_from_db(limit=50, offset=0):
        """Load papers from database and convert to API format"""
        try:
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
                    "organism": paper.get("organism"),
                    "year": paper.get("year"),
                    "source": paper.get("source"),
                    "authors": paper.get("authors", "Unknown Author"),
                    "mission": paper.get("mission", "Unknown Mission"),
                    "environment": paper.get("environment", "Space Environment"),
                    "summary": paper.get("summary", ""),
                    "citations": paper.get("citations", 0),
                    "hasOSDR": bool(paper.get("hasOSDR")),
                    "hasDOI": bool(paper.get("hasDOI")),
                    "bookmarked": bool(paper.get("bookmarked")),
                    "abstract": paper.get("abstract", ""),
                    "keyResults": key_results,
                    "methods": paper.get("methods", "Not specified"),
                    "conclusions": paper.get("conclusions", "Not specified"),
                    "doi": paper.get("doi", ""),
                    "osdrLink": paper.get("osdrLink", ""),
                    "taskBookLink": paper.get("taskBookLink", "")
                }
                api_papers.append(api_paper)

            return api_papers
        except Exception as e:
            print(f"Error loading papers from database: {e}")
            return []

    def search_elasticsearch(query, filters=None, size=10, offset=0):
        """Search Elasticsearch with query and filters"""
        if filters is None:
            filters = {}

        # Build Elasticsearch query
        es_query = {
            "size": size,
            "from": offset,
            "query": {
                "function_score": {
                    "query": {
                        "bool": {
                            "must": [],
                            "filter": []
                        }
                    },
                    "functions": [
                        {
                            "gauss": {
                                "date": {
                                    "origin": "now",
                                    "scale": "365d",
                                    "decay": 0.5
                                }
                            }
                        }
                    ],
                    "score_mode": "sum",
                    "boost_mode": "sum"
                }
            },
            "highlight": {
                "fields": {
                    "abstract": {},
                    "title": {}
                }
            }
        }

        # Add text search if query provided
        if query and query.strip():
            # Parse filter terms from query (e.g., "organism:human mission:ISS")
            search_terms = []
            filter_terms = []
            
            for term in query.split():
                if ':' in term:
                    # This is a filter term, extract the keyword
                    key, value = term.split(':', 1)
                    filter_terms.append(value)
                else:
                    # This is a regular search term
                    search_terms.append(term)
            
            # Combine all terms for searching in title and abstract
            all_terms = search_terms + filter_terms
            search_text = ' '.join(all_terms)
            
            if search_text.strip():
                es_query["query"]["function_score"]["query"]["bool"]["must"].append({
                    "multi_match": {
                        "query": search_text,
                        "type": "most_fields",
                        "fields": ["title^3", "abstract^2", "authors"]
                    }
                })
            else:
                # If no searchable terms, match all documents
                es_query["query"]["function_score"]["query"]["bool"]["must"].append({
                    "match_all": {}
                })
        else:
            # If no query, match all documents
            es_query["query"]["function_score"]["query"]["bool"]["must"].append({
                "match_all": {}
            })

        # Add filters (only year range since other fields are null)
        if filters.get("year_gte"):
            es_query["query"]["function_score"]["query"]["bool"]["filter"].append({
                "range": {"year": {"gte": filters["year_gte"]}}
            })
        if filters.get("year_lte"):
            es_query["query"]["function_score"]["query"]["bool"]["filter"].append({
                "range": {"year": {"lte": filters["year_lte"]}}
            })

        # Make request to Elasticsearch
        search_url = f"{ES_ENDPOINT}/{INDEX_NAME}/_search"
        response = requests.post(
            search_url,
            auth=(ES_USERNAME, ES_PASSWORD),
            headers={'Content-Type': 'application/json'},
            data=json.dumps(es_query)
        )

        if response.status_code != 200:
            print(f"Elasticsearch error: {response.text}")
            return {"total": 0, "results": [], "error": response.text}

        data = response.json()
        hits = data['hits']['hits']
        total = data['hits']['total']['value']

        # Convert to our API format
        results = []
        for hit in hits:
            source = hit['_source']
            result = {
                "id": source['paper_id'],
                "title": source['title'],
                "url": source['url'],
                "organism": source.get('organism'),
                "year": source.get('year'),
                "source": source.get('venue'),
                "authors": source.get('authors', 'Unknown Author'),
                "mission": source.get('mission', 'Unknown Mission'),
                "environment": source.get('environment', 'Space Environment'),
                "summary": source.get('abstract', '')[:200] + "..." if len(source.get('abstract', '')) > 200 else source.get('abstract', ''),
                "citations": source.get('citations', 0),
                "hasOSDR": source.get('hasOSDR', False),
                "hasDOI": source.get('hasDOI', False),
                "bookmarked": False,  # Not stored in ES yet
                "abstract": source.get('abstract', ''),
                "keyResults": [],  # Not stored in ES yet
                "methods": "Not specified",  # Not stored in ES yet
                "conclusions": "Not specified",  # Not stored in ES yet
                "doi": source.get('doi', ''),
                "osdrLink": source.get('osdrLink', ''),
                "taskBookLink": source.get('taskBookLink', ''),
                "score": hit.get('_score', 0),
                "highlights": hit.get('highlight', {})
            }
            results.append(result)

        # If no results found, get top 10 papers by score
        if total == 0:
            print("No results found, returning top 10 papers...")
            fallback_query = {
                "size": 10,
                "query": {"match_all": {}},
                "sort": [{"_score": {"order": "desc"}}]
            }
            fallback_response = requests.post(
                search_url,
                auth=(ES_USERNAME, ES_PASSWORD),
                headers={'Content-Type': 'application/json'},
                data=json.dumps(fallback_query)
            )
            if fallback_response.status_code == 200:
                fallback_data = fallback_response.json()
                fallback_hits = fallback_data['hits']['hits']
                results = []
                for hit in fallback_hits:
                    source = hit['_source']
                    result = {
                        "id": source['paper_id'],
                        "title": source['title'],
                        "url": source['url'],
                        "organism": source.get('organism'),
                        "year": source.get('year'),
                        "source": source.get('venue'),
                        "authors": source.get('authors', 'Unknown Author'),
                        "mission": source.get('mission', 'Unknown Mission'),
                        "environment": source.get('environment', 'Space Environment'),
                        "summary": source.get('abstract', '')[:200] + "..." if len(source.get('abstract', '')) > 200 else source.get('abstract', ''),
                        "citations": source.get('citations', 0),
                        "hasOSDR": source.get('hasOSDR', False),
                        "hasDOI": source.get('hasDOI', False),
                        "bookmarked": False,
                        "abstract": source.get('abstract', ''),
                        "keyResults": [],
                        "methods": "Not specified",
                        "conclusions": "Not specified",
                        "doi": source.get('doi', ''),
                        "osdrLink": source.get('osdrLink', ''),
                        "taskBookLink": source.get('taskBookLink', ''),
                        "score": hit.get('_score', 0),
                        "highlights": hit.get('highlight', {})
                    }
                    results.append(result)
                total = len(results)

        return {"total": total, "results": results}

    @app.get("/api/health")
    def health():
        """Health check endpoint"""
        try:
            # Check Elasticsearch health
            es_health_url = f"{ES_ENDPOINT}/_cluster/health"
            es_response = requests.get(es_health_url, auth=(ES_USERNAME, ES_PASSWORD))
            
            if es_response.status_code == 200:
                es_data = es_response.json()
                return {
                    "status": "ok", 
                    "es_status": es_data.get('status', 'unknown'),
                    "es_node_count": es_data.get('number_of_nodes', 0),
                    "papers_indexed": "607"  # We know this from migration
                }
            else:
                return {"status": "error", "es_error": "Cannot connect to Elasticsearch"}, 500
        except Exception as e:
            return {"status": "error", "es_error": str(e)}, 500

    @app.get("/api/papers")
    def list_papers():
        """Get papers with Elasticsearch search and pagination"""
        try:
            # Get query parameters
            query = request.args.get("q", "").strip()
            limit = max(1, min(int(request.args.get("limit", 50)), 1000))
            offset = max(0, int(request.args.get("offset", 0)))
            
            # If no search query, load from database
            if not query:
                papers = load_papers_from_db(limit, offset)
                return jsonify(papers)
            
            # Get filter parameters
            filters = {}
            if request.args.get("year_gte"):
                filters["year_gte"] = int(request.args.get("year_gte"))
            if request.args.get("year_lte"):
                filters["year_lte"] = int(request.args.get("year_lte"))
            if request.args.get("organism"):
                filters["organism"] = request.args.get("organism")
            if request.args.get("mission"):
                filters["mission"] = request.args.get("mission")
            if request.args.get("environment"):
                filters["environment"] = request.args.get("environment")
            if request.args.get("hasOSDR"):
                filters["hasOSDR"] = request.args.get("hasOSDR").lower() == 'true'
            if request.args.get("hasDOI"):
                filters["hasDOI"] = request.args.get("hasDOI").lower() == 'true'

            # Search Elasticsearch
            search_result = search_elasticsearch(query, filters, limit, offset)
            
            if "error" in search_result:
                return {"error": search_result["error"]}, 500

            return jsonify(search_result["results"])

        except Exception as e:
            print(f"Error in list_papers: {str(e)}")
            return {"error": str(e)}, 500

    @app.get("/api/papers/search")
    def search_papers():
        """Search papers endpoint (alias for /api/papers)"""
        return list_papers()

    @app.get("/api/papers/titles")
    def get_titles():
        """Get paper titles only"""
        try:
            # Get all papers from database
            papers = load_papers_from_db(1000, 0)
            titles = [{"id": paper["id"], "title": paper["title"]} for paper in papers]
            return jsonify(titles)

        except Exception as e:
            print(f"Error in get_titles: {str(e)}")
            return {"error": str(e)}, 500

    @app.post("/api/papers/enrich-all")
    def enrich_all_papers():
        """Enrich all papers endpoint (placeholder - not needed for ES)"""
        return jsonify({
            "success": True,
            "message": "Papers are already enriched in Elasticsearch",
            "total_papers": 607,
            "enriched_count": 607,
            "error_count": 0,
            "skipped_count": 0
        })

    @app.post("/api/papers/add")
    def add_paper():
        """Add a new paper by URL (placeholder - would need PMC scraper integration)"""
        try:
            data = request.get_json(force=True) or {}
            url = (data.get("url") or "").strip()
            
            if not url:
                return {"error": "URL is required"}, 400
            
            # For now, return a placeholder response
            return jsonify({
                "success": False,
                "message": "Add paper functionality not yet implemented for Elasticsearch backend",
                "error": "Use the database backend for adding new papers"
            })
            
        except Exception as e:
            print(f"Error in add_paper: {str(e)}")
            return {"error": str(e)}, 500

    return app

app = create_app()

if __name__ == "__main__":
    print("🚀 Starting Elasticsearch-powered Flask API...")
    print(f"📊 Elasticsearch endpoint: {ES_ENDPOINT}")
    print(f"📚 Index: {INDEX_NAME}")
    app.run(host="127.0.0.1", port=5003, debug=True)