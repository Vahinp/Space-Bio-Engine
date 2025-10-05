# ai.py
import os
import json
import requests
from typing import Callable, List, Dict, Tuple

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

# Azure config (optional)
AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "").rstrip("/")
AZURE_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")
AZURE_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-06-01")
AZURE_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")

# OpenAI (api.openai.com) config
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")

def _chat_complete(messages: List[Dict[str, str]], model: str) -> str:
    """
    Calls either Azure OpenAI (if AZURE_* present) or OpenAI (if OPENAI_API_KEY present).
    Prefers Azure when both are set.
    """
    if AZURE_ENDPOINT and AZURE_KEY:
        url = f"{AZURE_ENDPOINT}/openai/deployments/{AZURE_DEPLOYMENT}/chat/completions?api-version={AZURE_API_VERSION}"
        headers = {"api-key": AZURE_KEY, "Content-Type": "application/json"}
        payload = {"messages": messages, "temperature": 0.2, "max_tokens": 900}
        r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=45)
        r.raise_for_status()
        data = r.json()
        return data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()

    if not OPENAI_KEY:
        # No keys at all → very short local fallback
        return "AI is not configured (no API key found). Please set OPENAI_API_KEY or Azure OpenAI credentials."

    # OpenAI standard endpoint
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {OPENAI_KEY}", "Content-Type": "application/json"}
    payload = {"model": model, "messages": messages, "temperature": 0.2, "max_tokens": 900}
    r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=45)
    r.raise_for_status()
    data = r.json()
    return data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()


def answer_with_rag(query: str, search_fn: Callable[[str, int], List[Dict]], model: str = OPENAI_MODEL) -> Tuple[str, List[Dict]]:
    """
    Simple RAG:
    - search_fn(query, k) returns list of docs with fields: title, year, abstract, url, id
    - build a compact context and ask the model to answer with inline [#] citations.
    """
    top = search_fn(query, 6) or []
    context_lines = []
    for i, doc in enumerate(top, 1):
        ttl = (doc.get("title") or "Untitled").strip()
        yr  = doc.get("year") or "Unknown"
        absr = (doc.get("abstract") or "")[:600]
        url = doc.get("url") or ""
        context_lines.append(f"[{i}] {ttl} ({yr})\n{absr}\n{url}\n")

    system = {
        "role": "system",
        "content": (
            "You are an expert assistant for NASA space biology literature. "
            "Use the provided papers as trusted context. Cite sources as [1], [2], etc. "
            "Be concise but thorough. If uncertain, say what would be needed."
        )
    }
    user = {
        "role": "user",
        "content": (
            f"User question:\n{query}\n\n"
            f"Relevant papers:\n\n" + ("\n".join(context_lines) if context_lines else "None found.")
        )
    }

    reply = _chat_complete([system, user], model)
    # Attach compact source list for UI display
    sources = [{"n": i+1,
                "title": (d.get("title") or "Untitled"),
                "year": d.get("year"),
                "url": d.get("url"),
                "id": d.get("id")}
               for i, d in enumerate(top)]
    return reply, sources


def summarize_text(text: str, style: str = "keypoints", model: str = OPENAI_MODEL) -> str:
    prompt = (
        f"Summarize the following text from a space biology paper in '{style}' style. "
        "Prefer Results/Conclusions if present. Provide 5-8 compact bullets, then 1-2 gaps/future-work bullets."
    )
    messages = [
        {"role": "system", "content": "You are a scientific summarization assistant."},
        {"role": "user", "content": f"{prompt}\n\n---\n{text}\n---"}
    ]
    return _chat_complete(messages, model)
