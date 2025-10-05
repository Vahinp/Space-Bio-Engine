#!/usr/bin/env python3
"""
Flask API for Space Bio Engine with Elasticsearch backend + Chat + AI

- Loads env from .env (GEMINI_API_KEY, GEMINI_MODEL, ES_*)
- Dev-friendly CORS (handles OPTIONS preflight)
- Elasticsearch search with safe mapping + fallback
- Chat blueprint + Socket.IO (auto AI replies for threads of type="ai")
- AI endpoints:
    /api/ai/ping
    /api/ai/ask
    /api/ai/context
    /api/chat/context   (legacy alias to match your frontend)
    /api/ai/summarize
"""

import os
import json
import requests
from typing import Dict, Any, List

from flask import Flask, jsonify, request, Response
from flask_cors import CORS
from dotenv import load_dotenv
import google.generativeai as genai

# Load .env early (GEMINI_API_KEY, GEMINI_MODEL, ES_*)
load_dotenv()

# --- Local modules you already have ---
from database import (
    get_papers,
    get_papers_count,
    create_database,
    migrate_csv_to_database,
)
from chat import init_chat                 # registers /api/chat + initializes chat DB
from chat import socketio as _socketio     # socket server runner
from ai import answer_with_rag, summarize_text


# ------------------------------------------------------------------------------
# Config
# ------------------------------------------------------------------------------
ES_ENDPOINT = os.getenv("ES_ENDPOINT", "http://localhost:9200")
ES_USERNAME = os.getenv("ES_USERNAME", "elastic")
ES_PASSWORD = os.getenv("ES_PASSWORD", "elasSer12!")
INDEX_NAME  = os.getenv("ES_INDEX", "space_bio_papers")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyAFKyyGqKGWM0W2J1gPzRtmhzAYw6fHKhw")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")


# ------------------------------------------------------------------------------
# App Factory
# ------------------------------------------------------------------------------
def create_app():
    app = Flask(__name__)

    # Dev-friendly CORS (OK for localhost; restrict for prod)
    CORS(
        app,
        resources={r"/api/*": {"origins": "*"}},
        supports_credentials=True,
        methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )

    # ---- Bootstrap your SQLite (papers) DB once, and seed from CSV if empty ----
    create_database()
    if get_papers_count() == 0:
        migrate_csv_to_database(os.getenv("CSV_PATH", "data/papers.csv"))
    print(f"✅ Database ready with {get_papers_count()} papers")

    # ---- Attach Chat blueprint + its SQLite and Socket.IO to this app ----------
    init_chat(app)

    # ---- Helper: load papers from local DB (used when 'q' is empty) ------------
    def load_papers_from_db(limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        try:
            papers = get_papers(limit=limit, offset=offset)
            api_papers = []
            for paper in papers:
                # Parse keyResults JSON string (if present)
                key_results = []
                if paper.get("keyResults"):
                    try:
                        key_results = json.loads(paper["keyResults"])
                    except json.JSONDecodeError:
                        key_results = []

                api_papers.append({
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
                    "taskBookLink": paper.get("taskBookLink", ""),
                })
            return api_papers
        except Exception as e:
            print(f"Error loading papers from database: {e}")
            return []

    # ---- Helper: run a search against Elasticsearch ---------------------------
    def search_elasticsearch(query: str, filters=None, size=10, offset=0) -> Dict[str, Any]:
        if filters is None:
            filters = {}

        es_query = {
            "size": size,
            "from": offset,
            "query": {
                "function_score": {
                    "query": {
                        "bool": {
                            "must": [],
                            "should": [],
                            "filter": []
                        }
                    },
                    "functions": [
                        {
                            "gauss": {
                                "year": {
                                    "origin": 2025,
                                    "scale": 5,
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

        # Simple parsing of space-delimited terms (support "organism:human" etc.)
        if query and query.strip():
            search_terms = []
            filter_terms = []
            for term in query.split():
                if ":" in term:
                    _, value = term.split(":", 1)
                    filter_terms.append(value)
                else:
                    search_terms.append(term)
            all_terms = search_terms + filter_terms
            search_text = " ".join(all_terms).strip()
            if search_text:
                # Broader, recall-oriented query with fuzziness and OR semantics
                es_query["query"]["function_score"]["query"]["bool"]["must"].append({
                    "multi_match": {
                        "query": search_text,
                        "type": "most_fields",
                        "fields": ["title^4", "abstract^2", "keywords^1.5", "organism", "methods", "conclusions", "summary"],
                        "operator": "or",
                        "fuzziness": "AUTO",
                        "tie_breaker": 0.2
                    }
                })
                # Soft boost for near-phrase matches in title
                es_query["query"]["function_score"]["query"]["bool"]["should"].append({
                    "match_phrase": {"title": {"query": search_text, "slop": 2, "boost": 2.0}}
                })
            else:
                es_query["query"]["function_score"]["query"]["bool"]["must"].append({"match_all": {}})
        else:
            # No search text: only use match_all when there are no textual facets provided
            # If facets are present, facet clauses below will constrain results
            pass

        if filters.get("year_gte"):
            es_query["query"]["function_score"]["query"]["bool"]["filter"].append({
                "range": {"year": {"gte": filters["year_gte"]}}
            })
        if filters.get("year_lte"):
            es_query["query"]["function_score"]["query"]["bool"]["filter"].append({
                "range": {"year": {"lte": filters["year_lte"]}}
            })
        
        # Textual facet behavior:
        # - If one facet active: broaden (OR) — show anything related (should)
        # - If 2+ facets active: tighten (AND) — require mention of each facet (must)
        textual_facets = []
        for key in ("organism", "mission", "environment"):
            vals = filters.get(key)
            if vals:
                if not isinstance(vals, list):
                    vals = [vals]
                textual_facets.append((key, [v for v in vals if v]))

        if len(textual_facets) == 1:
            key, vals = textual_facets[0]
            # Single facet: require at least one reference to any of its values
            joined = " | ".join([str(v) for v in vals])
            es_query["query"]["function_score"]["query"]["bool"]["must"].append({
                "simple_query_string": {
                    "query": joined,
                    "fields": ["title^3", "abstract^2", f"{key}^2", "keywords", "summary", "methods", "conclusions"],
                    "default_operator": "or"
                }
            })
            # Phrase boosts for closer references
            for val in vals:
                es_query["query"]["function_score"]["query"]["bool"]["should"].append({"match_phrase": {"title": {"query": val, "slop": 3, "boost": 2.0}}})
                es_query["query"]["function_score"]["query"]["bool"]["should"].append({"match_phrase": {"abstract": {"query": val, "slop": 3, "boost": 1.3}}})
        elif len(textual_facets) >= 2:
            for key, vals in textual_facets:
                # For each facet, require at least one of its values (AND across facets)
                joined = " | ".join([str(v) for v in vals])
                es_query["query"]["function_score"]["query"]["bool"]["must"].append({
                    "simple_query_string": {
                        "query": joined,
                        "fields": ["title^2", "abstract^1.5", f"{key}^2", "keywords", "summary"],
                        "default_operator": "or"
                    }
                })
                # Phrase boosts per facet value
                for val in vals:
                    es_query["query"]["function_score"]["query"]["bool"]["should"].append({"match_phrase": {"title": {"query": val, "slop": 3, "boost": 1.6}}})
                    es_query["query"]["function_score"]["query"]["bool"]["should"].append({"match_phrase": {"abstract": {"query": val, "slop": 3, "boost": 1.2}}})

        # If still no query and no facets, use match_all to return something
        if not (query and query.strip()) and not textual_facets:
            es_query["query"]["function_score"]["query"]["bool"]["must"].append({"match_all": {}})

        # Only enforce truly binary facets strictly if requested true
        if "hasOSDR" in filters and filters.get("hasOSDR") is not None:
            es_query["query"]["function_score"]["query"]["bool"]["filter"].append({
                "term": {"hasOSDR": bool(filters["hasOSDR"]) }
            })
        if "hasDOI" in filters and filters.get("hasDOI") is not None and filters["hasDOI"]:
            es_query["query"]["function_score"]["query"]["bool"]["filter"].append({
                "exists": {"field": "doi"}
            })
        # Avoid strict keyword term filters on textual facets to prevent over-narrowing
        # Only apply strict binary flags here
        if "hasOSDR" in filters and filters.get("hasOSDR") is not None:
            es_query["query"]["function_score"]["query"]["bool"]["filter"].append({
                "term": {"hasOSDR": bool(filters["hasOSDR"]) }
            })
        if "hasDOI" in filters and filters.get("hasDOI") is not None and filters["hasDOI"]:
            es_query["query"]["function_score"]["query"]["bool"]["filter"].append({
                "exists": {"field": "doi"}
            })

        search_url = f"{ES_ENDPOINT}/{INDEX_NAME}/_search"
        try:
            response = requests.post(
                search_url,
                auth=(ES_USERNAME, ES_PASSWORD),
                headers={"Content-Type": "application/json"},
                data=json.dumps(es_query),
                timeout=20,
            )
        except Exception as e:
            print(f"Elasticsearch request error: {e}")
            return {"total": 0, "results": [], "error": str(e)}

        if response.status_code != 200:
            print(f"Elasticsearch error: {response.text}")
            return {"total": 0, "results": [], "error": response.text}

        data = response.json()
        hits = data.get("hits", {}).get("hits", [])
        total = data.get("hits", {}).get("total", {}).get("value", 0)

        def to_api_result(hit: Dict[str, Any]) -> Dict[str, Any]:
            source = hit.get("_source", {}) or {}
            abstract = source.get("abstract", "") or ""
            return {
                "id": source.get("paper_id") or source.get("id"),
                "title": source.get("title"),
                "url": source.get("url"),
                "organism": source.get("organism"),
                "year": source.get("year"),
                "source": source.get("venue") or source.get("source"),
                "authors": source.get("authors", "Unknown Author"),
                "mission": source.get("mission", "Unknown Mission"),
                "environment": source.get("environment", "Space Environment"),
                "summary": (abstract[:200] + "...") if len(abstract) > 200 else abstract,
                "citations": source.get("citations", 0),
                "hasOSDR": bool(source.get("hasOSDR", False)),
                "hasDOI": bool(source.get("hasDOI", False)),
                "bookmarked": False,
                "abstract": abstract,
                "keyResults": [],
                "methods": "Not specified",
                "conclusions": "Not specified",
                "doi": source.get("doi", ""),
                "osdrLink": source.get("osdrLink", ""),
                "taskBookLink": source.get("taskBookLink", ""),
                "score": hit.get("_score", 0),
                "highlights": hit.get("highlight", {})
            }

        # Convert and de-duplicate results by id+url to avoid repeats
        results = [to_api_result(h) for h in hits]
        seen = set()
        deduped = []
        for r in results:
            key = f"{r.get('id') or ''}::{r.get('url') or ''}"
            if key in seen:
                continue
            seen.add(key)
            deduped.append(r)

        # If recall is too low, run a relaxed, highly permissive query and merge
        if total < max(5, size // 3):
            relaxed = {
                "size": size,
                "from": 0,
                "query": {
                    "bool": {
                        "should": [
                            {"multi_match": {
                                "query": query,
                                "type": "best_fields",
                                "fields": ["title^4", "abstract^2", "keywords^1.5", "summary", "methods", "conclusions", "authors"],
                                "operator": "or",
                                "fuzziness": "AUTO",
                                "prefix_length": 0,
                                "tie_breaker": 0.3
                            }},
                            {"match": {"abstract": {"query": query, "fuzziness": "AUTO", "boost": 1.2}}},
                            {"match": {"title": {"query": query, "fuzziness": "AUTO", "boost": 1.5}}}
                        ],
                        "filter": es_query["query"]["function_score"]["query"]["bool"].get("filter", [])
                    }
                },
            }
            try:
                rresp = requests.post(
                    search_url,
                    auth=(ES_USERNAME, ES_PASSWORD),
                    headers={"Content-Type": "application/json"},
                    data=json.dumps(relaxed),
                    timeout=20,
                )
                if rresp.status_code == 200:
                    rhits = rresp.json().get("hits", {}).get("hits", [])
                    for h in rhits:
                        r = to_api_result(h)
                        key = f"{r.get('id') or ''}::{r.get('url') or ''}"
                        if key in seen:
                            continue
                        seen.add(key)
                        deduped.append(r)
                    total = len(deduped)
            except Exception as e:
                print(f"Relaxed search failed: {e}")

        # Strong fallback: return a larger set if still empty
        if total == 0:
            print("No results found, returning top 10 papers...")
            fallback_query = {"size": max(30, size), "query": {"match_all": {}}, "sort": [{"year": {"order": "desc"}}]}
            fallback_response = requests.post(
                search_url,
                auth=(ES_USERNAME, ES_PASSWORD),
                headers={"Content-Type": "application/json"},
                data=json.dumps(fallback_query),
                timeout=20,
            )
            if fallback_response.status_code == 200:
                fallback_hits = fallback_response.json().get("hits", {}).get("hits", [])
                fallback_results = [to_api_result(h) for h in fallback_hits]
                # Deduplicate fallback as well
                seen_fb = set()
                deduped_fb = []
                for r in fallback_results:
                    key = f"{r.get('id') or ''}::{r.get('url') or ''}"
                    if key in seen_fb:
                        continue
                    seen_fb.add(key)
                    deduped_fb.append(r)
                deduped = deduped_fb
                total = len(deduped)

        return {"total": total, "results": deduped}

    # Make search helper visible to AI module via closure
    def search_top_k(query: str, k: int = 6) -> List[Dict[str, Any]]:
        sr = search_elasticsearch(query, size=k, offset=0)
        return sr.get("results", [])

    

    # --------------------------------------------------------------------------
    # Wire AI reply function into chat
    # --------------------------------------------------------------------------
    def ai_reply_fn(thread, recent_messages):
        last_user = ""
        for m in reversed(recent_messages):
            if m.sender != "assistant":
                last_user = (m.content or "").strip()
                break

        if not last_user:
            return {"content": "How can I help you explore NASA bioscience research today?"}

        answer, sources = answer_with_rag(
            query=last_user,
            search_fn=search_top_k,
            model=GEMINI_MODEL,
        )
        return {"content": answer, "sources": sources}

    app.config["AI_REPLY_FN"] = ai_reply_fn

    # ------------------------------------------------------------------------------
    # Routes
    # ------------------------------------------------------------------------------
    @app.get("/api/health")
    def health():
        try:
            es_health_url = f"{ES_ENDPOINT}/_cluster/health"
            es_response = requests.get(es_health_url, auth=(ES_USERNAME, ES_PASSWORD), timeout=10)
            if es_response.status_code == 200:
                es_data = es_response.json()
                return {
                    "status": "ok",
                    "es_status": es_data.get("status", "unknown"),
                    "es_node_count": es_data.get("number_of_nodes", 0),
                    "papers_indexed": "607",
                }
            return {"status": "error", "es_error": "Cannot connect to Elasticsearch"}, 500
        except Exception as e:
            return {"status": "error", "es_error": str(e)}, 500

    @app.get("/api/papers")
    def list_papers():
        try:
            query = (request.args.get("q") or "").strip()
            limit = max(1, min(int(request.args.get("limit", 50)), 5000))
            offset = max(0, int(request.args.get("offset", 0)))

            # Detect if any filters are present; if so, use Elasticsearch even when query is empty
            has_filter_params = any([
                request.args.get("year_gte"),
                request.args.get("year_lte"),
                request.args.get("organism"),
                request.args.get("mission"),
                request.args.get("environment"),
                request.args.get("hasOSDR"),
                request.args.get("hasDOI"),
            ])

            if not query and not has_filter_params:
                papers = load_papers_from_db(limit, offset)
                return jsonify(papers)

            filters = {}
            if request.args.get("year_gte"):
                filters["year_gte"] = int(request.args.get("year_gte"))
            if request.args.get("year_lte"):
                filters["year_lte"] = int(request.args.get("year_lte"))
            # Facets can be comma-separated lists; store as arrays
            def _split_vals(v: str):
                return [s.strip() for s in (v or "").split(",") if s.strip()]
            if request.args.get("organism"):
                filters["organism"] = _split_vals(request.args.get("organism"))
            if request.args.get("mission"):
                filters["mission"] = _split_vals(request.args.get("mission"))
            if request.args.get("environment"):
                filters["environment"] = _split_vals(request.args.get("environment"))
            if request.args.get("hasOSDR") is not None:
                val = request.args.get("hasOSDR")
                filters["hasOSDR"] = val in ("1", "true", "True", "yes")
            if request.args.get("hasDOI") is not None:
                val = request.args.get("hasDOI")
                filters["hasDOI"] = val in ("1", "true", "True", "yes")

            # If query is empty but filters exist, pass empty string to trigger match_all with filters
            search_result = search_elasticsearch(query or "", filters, limit, offset)
            if "error" in search_result:
                return {"error": search_result["error"]}, 500
            return jsonify(search_result["results"])
        except Exception as e:
            print(f"Error in list_papers: {e}")
            return {"error": str(e)}, 500

    @app.get("/api/papers/search")
    def search_papers():
        return list_papers()

    # Yearly stats (counts by year) honoring same filters as search
    @app.get("/api/stats/yearly")
    def stats_yearly():
        try:
            query = (request.args.get("q") or "").strip()
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
            if request.args.get("hasOSDR") is not None:
                val = request.args.get("hasOSDR")
                filters["hasOSDR"] = val in ("1", "true", "True", "yes")
            if request.args.get("hasDOI") is not None:
                val = request.args.get("hasDOI")
                filters["hasDOI"] = val in ("1", "true", "True", "yes")

            # Build ES query analogous to search_elasticsearch()
            es_query = {
                "size": 0,
                "query": {
                    "bool": {
                        "must": [],
                        "filter": []
                    }
                },
                "aggs": {
                    "by_year": {
                        "terms": {
                            "field": "year",
                            "size": 1000,
                            "order": {"_key": "asc"}
                        }
                    }
                }
            }

            if query and query.strip():
                es_query["query"]["bool"]["must"].append({
                    "multi_match": {
                        "query": query,
                        "type": "most_fields",
                        "fields": ["title^3", "abstract^2", "authors"]
                    }
                })
            else:
                es_query["query"]["bool"]["must"].append({"match_all": {}})

            if filters.get("year_gte"):
                es_query["query"]["bool"]["filter"].append({"range": {"year": {"gte": filters["year_gte"]}}})
            if filters.get("year_lte"):
                es_query["query"]["bool"]["filter"].append({"range": {"year": {"lte": filters["year_lte"]}}})
            if filters.get("organism"):
                org_val = filters["organism"]
                if isinstance(org_val, list):
                    es_query["query"]["bool"]["filter"].append({"terms": {"organism.keyword": org_val}})
                else:
                    es_query["query"]["bool"]["filter"].append({"term": {"organism.keyword": org_val}})
            if filters.get("mission"):
                mis_val = filters["mission"]
                if isinstance(mis_val, list):
                    es_query["query"]["bool"]["filter"].append({"terms": {"mission.keyword": mis_val}})
                else:
                    es_query["query"]["bool"]["filter"].append({"term": {"mission.keyword": mis_val}})
            if filters.get("environment"):
                env_val = filters["environment"]
                if isinstance(env_val, list):
                    es_query["query"]["bool"]["filter"].append({"terms": {"environment.keyword": env_val}})
                else:
                    es_query["query"]["bool"]["filter"].append({"term": {"environment.keyword": env_val}})
            if "hasOSDR" in filters and filters.get("hasOSDR") is not None:
                es_query["query"]["bool"]["filter"].append({"term": {"hasOSDR": bool(filters["hasOSDR"])}})
            if "hasDOI" in filters and filters.get("hasDOI") is not None:
                if filters["hasDOI"]:
                    es_query["query"]["bool"]["filter"].append({"exists": {"field": "doi"}})

            url = f"{ES_ENDPOINT}/{INDEX_NAME}/_search"
            rsp = requests.post(
                url,
                auth=(ES_USERNAME, ES_PASSWORD),
                headers={"Content-Type": "application/json"},
                data=json.dumps(es_query),
                timeout=20,
            )
            if rsp.status_code != 200:
                return {"error": rsp.text}, 500
            data = rsp.json()
            buckets = (((data.get("aggregations") or {}).get("by_year") or {}).get("buckets") or [])
            counts = { str(b.get("key")): int(b.get("doc_count")) for b in buckets }
            # Sorted by year asc
            counts_sorted = dict(sorted(counts.items(), key=lambda kv: int(kv[0])))
            return jsonify({"counts": counts_sorted})
        except Exception as e:
            print(f"Error in stats_yearly: {e}")
            return {"error": str(e)}, 500

    @app.get("/api/papers/titles")
    def get_titles():
        try:
            papers = load_papers_from_db(1000, 0)
            titles = [{"id": paper["id"], "title": paper["title"]} for paper in papers]
            return jsonify(titles)
        except Exception as e:
            print(f"Error in get_titles: {e}")
            return {"error": str(e)}, 500

    # ---------------- AI endpoints ----------------

    @app.get("/api/ai/ping")
    def ai_ping():
        return jsonify({
            "ok": True,
            "has_key": bool(GEMINI_API_KEY),
            "model": GEMINI_MODEL
        })

    @app.post("/api/ai/ask")
    def ai_ask():
        data = request.get_json(force=True) or {}
        q = (data.get("query") or "").strip()
        if not q:
            return {"error": "query is required"}, 400
        try:
            answer, sources = answer_with_rag(q, search_top_k, GEMINI_MODEL)
            return jsonify({"answer": answer, "sources": sources})
        except Exception as e:
            print(f"[AI_ASK_ERROR] {e}")
            return jsonify({"error": "AI backend failed", "detail": str(e)}), 502

    @app.post("/api/ai/context")
    def ai_context():
        data = request.get_json(force=True) or {}
        q = (
            data.get("query")
            or data.get("prompt")
            or data.get("message")
            or data.get("text")
            or ""
        ).strip()
        if not q:
            return {"error": "query is required"}, 400
        try:
            answer, sources = answer_with_rag(q, search_top_k, GEMINI_MODEL)
            return jsonify({"answer": answer, "sources": sources})
        except Exception as e:
            print(f"[AI_CONTEXT_ERROR] {e}")
            return jsonify({"error": "AI backend failed", "detail": str(e)}), 502

    # Legacy alias to match your frontend's current path: /api/chat/context
    @app.post("/api/chat/context")
    def ai_context_legacy():
        data = request.get_json(force=True) or {}
        q = (
            data.get("query")
            or data.get("prompt")
            or data.get("message")
            or data.get("text")
            or ""
        ).strip()
        if not q:
            return {"error": "query is required"}, 400
        try:
            answer, sources = answer_with_rag(q, search_top_k, GEMINI_MODEL)
            return jsonify({"answer": answer, "sources": sources})
        except Exception as e:
            print(f"[AI_CONTEXT_LEGACY_ERROR] {e}")
            return jsonify({"error": "AI backend failed", "detail": str(e)}), 502

    @app.post("/api/ai/summarize")
    def ai_summarize():
        data = request.get_json(force=True) or {}
        text = (data.get("text") or "").strip()
        style = (data.get("style") or "keypoints").strip()
        if not text:
            return {"error": "text is required"}, 400
        try:
            summary = summarize_text(text=text, style=style, model=GEMINI_MODEL)
            return jsonify({"summary": summary})
        except Exception as e:
            print(f"[AI_SUMMARY_ERROR] {e}")
            return jsonify({"error": "AI backend failed", "detail": str(e)}), 502

    @app.post("/api/papers/enrich-all")
    def enrich_all_papers():
        return jsonify({
            "success": True,
            "message": "Papers are already enriched in Elasticsearch",
            "total_papers": 607,
            "enriched_count": 607,
            "error_count": 0,
            "skipped_count": 0,
        })

    @app.post("/api/papers/add")
    def add_paper():
        try:
            data = request.get_json(force=True) or {}
            url = (data.get("url") or "").strip()
            if not url:
                return {"error": "URL is required"}, 400

            return jsonify({
                "success": False,
                "message": "Add paper functionality not yet implemented for Elasticsearch backend",
                "error": "Use the database backend for adding new papers",
            })
        except Exception as e:
            print(f"Error in add_paper: {e}")
            return {"error": str(e)}, 500

    # ------------------------------------------------------------------------------
    # OpenAI Chatbot Endpoints
    # ------------------------------------------------------------------------------
    
    # Initialize Gemini client with proper error handling
    if not GEMINI_API_KEY:
        print("⚠️  Warning: GEMINI_API_KEY not found. AI features will be disabled.")
        gemini_client = None
    else:
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            print(f"🔧 Using Gemini model: {GEMINI_MODEL}")
            gemini_client = genai.GenerativeModel(GEMINI_MODEL)
            print("✅ Gemini client initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize Gemini client: {e}")
            gemini_client = None
    
    def safe_extract_text_from_response(response):
        """Safely extract text from Gemini response regardless of finish_reason"""
        try:
            # First try the simple approach
            if hasattr(response, 'text') and response.text:
                return response.text
        except:
            pass
        
        # If that fails, try to extract from candidates
        try:
            if hasattr(response, 'candidates') and response.candidates:
                for candidate in response.candidates:
                    # Try direct parts access
                    if hasattr(candidate, 'parts') and candidate.parts:
                        text_parts = []
                        for part in candidate.parts:
                            if hasattr(part, 'text') and part.text:
                                text_parts.append(part.text)
                        if text_parts:
                            return ' '.join(text_parts)
                    
                    # Try content.parts access
                    if hasattr(candidate, 'content') and candidate.content:
                        if hasattr(candidate.content, 'parts') and candidate.content.parts:
                            text_parts = []
                            for part in candidate.content.parts:
                                if hasattr(part, 'text') and part.text:
                                    text_parts.append(part.text)
                            if text_parts:
                                return ' '.join(text_parts)
        except:
            pass
        
        return None

    @app.post("/api/chat")
    def chat():
        """Chat endpoint that uses RAG to answer with sources (title + link)."""
        try:
            data = request.get_json(force=True) or {}
            # Accept either full chat messages or a simple query field
            if isinstance(data.get("messages"), list) and data["messages"]:
                # Extract last user message
                last_user = ""
                for m in reversed(data["messages"]):
                    if (m or {}).get("role") != "assistant":
                        last_user = ((m or {}).get("content") or "").strip()
                        if last_user:
                            break
                query = last_user
            else:
                query = (data.get("query") or data.get("text") or "").strip()

            if not query:
                return jsonify({"answer": "How can I help you explore NASA bioscience research today?"})

            answer, sources = answer_with_rag(
                query=query,
                search_fn=search_top_k,
                model=GEMINI_MODEL,
            )

            # Build brief summaries for each source using its abstract
            source_summaries = []
            try:
                retrieved = search_top_k(query, 6)
                # Map retrieved docs by title+url for alignment
                def _key(d):
                    return f"{(d.get('title') or '').strip()}::{(d.get('url') or '').strip()}"
                key_to_doc = { _key(d): d for d in (retrieved or []) }
                for s in (sources or []):
                    k = _key(s)
                    doc = key_to_doc.get(k)
                    abstract = (doc or {}).get('abstract') or ''
                    title = s.get('title') or 'Untitled'
                    url = s.get('url') or ''
                    if abstract:
                        summary = summarize_text(
                            text=f"Title: {title}\nAbstract: {abstract}\n\nSummarize the abstract above in 1-2 concise sentences focusing on objectives and findings.",
                            style="concise"
                        )
                    else:
                        summary = "No abstract available to summarize."
                    source_summaries.append({
                        "n": s.get("n"),
                        "title": title,
                        "url": url,
                        "summary": summary.strip()
                    })
            except Exception as _e:
                print(f"[CHAT_SOURCE_SUMMARY_WARN] {_e}")

            # Also append plain-text sources and summaries for UIs that don't render lists
            if sources:
                lines = [answer.strip(), "", "Sources:"]
                for s in sources:
                    ttl = s.get("title") or "Untitled"
                    url = s.get("url") or ""
                    lines.append(f"- {ttl}{' — ' + url if url else ''}")
                if source_summaries:
                    lines.append("")
                    lines.append("Brief summaries:")
                    for ss in source_summaries:
                        lines.append(f"- {ss.get('title')} — {ss.get('summary')}")
                answer_text = "\n".join(lines)
            else:
                answer_text = answer

            return jsonify({"answer": answer_text, "sources": sources, "source_summaries": source_summaries})
        except Exception as e:
            print(f"[CHAT_ERROR] {e}")
            return jsonify({"error": "Chat service failed", "detail": str(e)}), 500

    @app.post("/api/chat-stream")
    def chat_stream():
        """Bulletproof streaming chat endpoint"""
        if not gemini_client:
            def generate_error():
                yield f"event: error\ndata: {json.dumps({'error': 'Gemini client not available. Please set GEMINI_API_KEY environment variable.'})}\n\n"
            return Response(
                generate_error(),
                mimetype='text/event-stream',
                headers={
                    'Cache-Control': 'no-cache',
                    'Connection': 'keep-alive',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type'
                }
            )
            
        data = request.get_json(force=True) or {}
        messages = data.get("messages", [{"role": "user", "content": "Hello!"}])
        
        def generate():
            try:
                # Build conversation text
                system_prompt = "You are a NASA space biology research assistant. You help researchers understand the effects of spaceflight on biological systems. You can discuss scientific topics including bone density, muscle loss, cardiovascular changes, and other physiological effects of microgravity. Please provide accurate, scientific information based on research findings."
                conversation_text = system_prompt + "\n\n"
                for message in messages:
                    if message.get("role") == "user":
                        conversation_text += f"User: {message.get('content', '')}\n"
                    elif message.get("role") == "assistant":
                        conversation_text += f"Assistant: {message.get('content', '')}\n"
                
                # Generate response
                response = gemini_client.generate_content(
                    conversation_text,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.1,
                        max_output_tokens=1000,
                        top_p=0.8,
                        top_k=40
                    )
                )
                
                # Extract text safely
                response_text = safe_extract_text_from_response(response)
                
                if not response_text:
                    # Provide helpful fallback messages
                    if hasattr(response, 'candidates') and response.candidates:
                        candidate = response.candidates[0]
                        finish_reason = getattr(candidate, 'finish_reason', 0)
                        
                        if finish_reason == 2:
                            response_text = "I apologize, but my response was cut off due to length limits. Please try asking a more specific question."
                        elif finish_reason == 3:
                            response_text = "I'm unable to provide a response to this query due to content safety guidelines. Please try rephrasing your question."
                        elif finish_reason == 4:
                            response_text = "I'm unable to provide a response to this query due to content policy restrictions. Please try a different question."
                        else:
                            response_text = f"I encountered an issue processing your request (code: {finish_reason}). Please try rephrasing your question."
                    else:
                        response_text = "I'm sorry, I couldn't generate a response. Please try again with a different question."
                
                # Simulate streaming by sending the response in chunks
                if response_text:
                    words = response_text.split()
                    for i, word in enumerate(words):
                        content = word + (" " if i < len(words) - 1 else "")
                        yield f"data: {json.dumps({'content': content})}\n\n"
                
                # Send completion signal
                yield "event: done\ndata: {}\n\n"
                
            except Exception as e:
                print(f"[CHAT_STREAM_ERROR] {e}")
                yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
        
        return Response(
            generate(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type'
            }
        )

    return app


# ------------------------------------------------------------------------------
# Entrypoint
# ------------------------------------------------------------------------------
app = create_app()

if __name__ == "__main__":
    print("🚀 Starting Elasticsearch-powered Flask API + Chat + AI...")
    print(f"📊 Elasticsearch endpoint: {ES_ENDPOINT}")
    print(f"📚 Index: {INDEX_NAME}")
    print(f"🧠 Gemini model: {GEMINI_MODEL}")
    # IMPORTANT: run via Socket.IO so websockets work
    # Using port 5001 to match your frontend's request: http://localhost:5001/api/chat/context
    _socketio.run(app, host="127.0.0.1", port=5003, debug=True, allow_unsafe_werkzeug=True)
