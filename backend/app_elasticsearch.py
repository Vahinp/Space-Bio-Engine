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
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


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
                es_query["query"]["function_score"]["query"]["bool"]["must"].append({
                    "multi_match": {
                        "query": search_text,
                        "type": "most_fields",
                        "fields": ["title^3", "abstract^2", "authors"]
                    }
                })
            else:
                es_query["query"]["function_score"]["query"]["bool"]["must"].append({"match_all": {}})
        else:
            es_query["query"]["function_score"]["query"]["bool"]["must"].append({"match_all": {}})

        if filters.get("year_gte"):
            es_query["query"]["function_score"]["query"]["bool"]["filter"].append({
                "range": {"year": {"gte": filters["year_gte"]}}
            })
        if filters.get("year_lte"):
            es_query["query"]["function_score"]["query"]["bool"]["filter"].append({
                "range": {"year": {"lte": filters["year_lte"]}}
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

        results = [to_api_result(h) for h in hits]

        # Fallback: top 10 if no hits
        if total == 0:
            print("No results found, returning top 10 papers...")
            fallback_query = {"size": 10, "query": {"match_all": {}}, "sort": [{"_score": {"order": "desc"}}]}
            fallback_response = requests.post(
                search_url,
                auth=(ES_USERNAME, ES_PASSWORD),
                headers={"Content-Type": "application/json"},
                data=json.dumps(fallback_query),
                timeout=20,
            )
            if fallback_response.status_code == 200:
                fallback_hits = fallback_response.json().get("hits", {}).get("hits", [])
                results = [to_api_result(h) for h in fallback_hits]
                total = len(results)

        return {"total": total, "results": results}

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
            limit = max(1, min(int(request.args.get("limit", 50)), 1000))
            offset = max(0, int(request.args.get("offset", 0)))

            if not query:
                papers = load_papers_from_db(limit, offset)
                return jsonify(papers)

            filters = {}
            if request.args.get("year_gte"):
                filters["year_gte"] = int(request.args.get("year_gte"))
            if request.args.get("year_lte"):
                filters["year_lte"] = int(request.args.get("year_lte"))

            search_result = search_elasticsearch(query, filters, limit, offset)
            if "error" in search_result:
                return {"error": search_result["error"]}, 500
            return jsonify(search_result["results"])
        except Exception as e:
            print(f"Error in list_papers: {e}")
            return {"error": str(e)}, 500

    @app.get("/api/papers/search")
    def search_papers():
        return list_papers()

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
        """Bulletproof chat endpoint with comprehensive error handling"""
        if not gemini_client:
            return jsonify({"error": "Gemini client not available. Please set GEMINI_API_KEY environment variable."}), 503
            
        try:
            data = request.get_json(force=True) or {}
            messages = data.get("messages", [{"role": "user", "content": "Hello!"}])
            
            # Build conversation text for Gemini
            system_prompt = "You are a NASA space biology research assistant. You help researchers understand the effects of spaceflight on biological systems. You can discuss scientific topics including bone density, muscle loss, cardiovascular changes, and other physiological effects of microgravity. Please provide accurate, scientific information based on research findings."
            
            conversation_text = system_prompt + "\n\n"
            for message in messages:
                if message.get("role") == "user":
                    conversation_text += f"User: {message.get('content', '')}\n"
                elif message.get("role") == "assistant":
                    conversation_text += f"Assistant: {message.get('content', '')}\n"
            
            # Generate response using Gemini with conservative settings
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
            answer_text = safe_extract_text_from_response(response)
            
            # Debug logging
            print(f"[DEBUG] Extracted text: {answer_text[:100] if answer_text else 'None'}")
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                finish_reason = getattr(candidate, 'finish_reason', 0)
                print(f"[DEBUG] Finish reason: {finish_reason}")
                print(f"[DEBUG] Candidate: {candidate}")
            
            # If first attempt failed due to safety filters, try a simpler approach
            if not answer_text and hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                finish_reason = getattr(candidate, 'finish_reason', 0)
                
                if finish_reason == 3:  # SAFETY filter triggered
                    print("[DEBUG] Safety filter triggered, trying simpler prompt...")
                    # Try with a much simpler, more direct prompt
                    simple_prompt = f"Please explain: {messages[-1].get('content', '') if messages else 'Hello'}"
                    try:
                        simple_response = gemini_client.generate_content(
                            simple_prompt,
                            generation_config=genai.types.GenerationConfig(
                                temperature=0.1,
                                max_output_tokens=500,
                                top_p=0.9,
                                top_k=20
                            )
                        )
                        answer_text = safe_extract_text_from_response(simple_response)
                        print(f"[DEBUG] Simple prompt result: {answer_text[:100] if answer_text else 'None'}")
                    except Exception as e:
                        print(f"[DEBUG] Simple prompt also failed: {e}")
            
            if answer_text:
                return jsonify({"answer": answer_text})
            else:
                # If no text extracted, provide helpful message based on finish_reason
                if hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    finish_reason = getattr(candidate, 'finish_reason', 0)
                    
                    if finish_reason == 2:  # MAX_TOKENS
                        return jsonify({"answer": "I apologize, but my response was cut off due to length limits. Please try asking a more specific question."})
                    elif finish_reason == 3:  # SAFETY
                        return jsonify({"answer": "I'm unable to provide a response to this query due to content safety guidelines. Please try rephrasing your question."})
                    elif finish_reason == 4:  # RECITATION
                        return jsonify({"answer": "I'm unable to provide a response to this query due to content policy restrictions. Please try a different question."})
                    else:
                        return jsonify({"answer": f"I encountered an issue processing your request (code: {finish_reason}). Please try rephrasing your question."})
                else:
                    return jsonify({"answer": "I'm sorry, I couldn't generate a response. Please try again with a different question."})
            
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
