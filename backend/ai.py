# ai.py
import os
from typing import Callable, List, Dict, Tuple

import google.generativeai as genai

# Defaults (overridable by env)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyAFKyyGqKGWM0W2J1gPzRtmhzAYw6fHKhw")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

# Configure Gemini client once
_client_ready = False
_model = None

def _init_client():
	"""Initialize Gemini client if not already initialized."""
	global _client_ready, _model
	if _client_ready:
		return
	if not GEMINI_API_KEY:
		raise RuntimeError("GEMINI_API_KEY not set")
	genai.configure(api_key=GEMINI_API_KEY)
	_model = genai.GenerativeModel(GEMINI_MODEL)
	_client_ready = True


def _chat_complete(prompt: str, temperature: float = 0.2, max_tokens: int = 900) -> str:
	_init_client()
	resp = _model.generate_content(
		prompt,
		generation_config=genai.types.GenerationConfig(
			temperature=temperature,
			max_output_tokens=max_tokens,
			top_p=0.9,
			top_k=40,
		),
	)
	# Robust extraction
	try:
		if hasattr(resp, "text") and resp.text:
			return resp.text.strip()
	except Exception:
		pass
	# Fallback: pull from candidates/parts
	try:
		if hasattr(resp, "candidates") and resp.candidates:
			cand = resp.candidates[0]
			parts = []
			for part in getattr(cand, "parts", []) or getattr(getattr(cand, "content", None), "parts", []) or []:
				t = getattr(part, "text", None)
				if t:
					parts.append(t)
			if parts:
				return " ".join(parts).strip()
	except Exception:
		pass
	return ""


def answer_with_rag(query: str, search_fn: Callable[[str, int], List[Dict]], model: str = GEMINI_MODEL) -> Tuple[str, List[Dict]]:
	"""
	RAG helper:
	- search_fn(query, k) returns list of docs with: title, year, abstract, url, id
	- Builds compact context and asks Gemini to answer with inline [#] citations.
	"""
	top = search_fn(query, 6) or []
	context_lines = []
	for i, doc in enumerate(top, 1):
		title = (doc.get("title") or "Untitled").strip()
		year  = doc.get("year") or "Unknown"
		abstract = (doc.get("abstract") or "")[:900]
		url = doc.get("url") or ""
		context_lines.append(f"[{i}] {title} ({year})\n{abstract}\n{url}\n")

	system = (
		"You are an expert assistant for NASA space biology literature.\n"
		"Use ONLY the provided abstracts as context. Cite sources inline as [1], [2], etc.\n"
		"If uncertain, state what additional information would be needed."
	)
	user = f"User question:\n{query}\n\nRelevant papers:\n\n" + ("\n".join(context_lines) if context_lines else "None found.")

	reply = _chat_complete(f"{system}\n\n{user}", temperature=0.2, max_tokens=1000)

	# Attach sources for UI display
	sources = [{
		"n": i + 1,
		"title": (d.get("title") or "Untitled"),
		"year": d.get("year"),
		"url": d.get("url"),
		"id": d.get("id")
	} for i, d in enumerate(top)]

	if not reply and not sources:
		reply = "I couldn't find enough evidence in the abstracts to answer confidently."
	return reply, sources


def summarize_text(text: str, style: str = "keypoints", model: str = GEMINI_MODEL) -> str:
	"""
	Lightweight, general-purpose summarizer for arbitrary text.
	"""
	system = (
		"You are summarizing NASA space biology research content. "
		"Be concise and include key findings and limitations."
	)
	prompt = (
		f"{system}\n\nSummarize in '{style}' style.\n\n"
		f"Content:\n{text.strip()}\n"
	)
	return _chat_complete(prompt, temperature=0.2, max_tokens=1200)