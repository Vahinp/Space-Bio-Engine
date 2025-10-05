# ai.py
"""
OpenAI helpers + lightweight RAG for NASA Space Biology.
Uses:
  - Environment: OPENAI_API_KEY (required), OPENAI_API_BASE (optional), OPENAI_MODEL (optional)
  - Minimal dependencies: requests
"""

import os
import textwrap
import requests
from typing import Callable, Dict, Any, List, Tuple

OPENAI_API_KEY  = os.getenv("OPENAI_API_KEY", "")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")  # override for azure if needed

def _post_chat(messages: List[Dict[str, str]], model: str = "gpt-4o-mini", temperature: float = 0.2) -> str:
    """
    Calls OpenAI chat completions endpoint via requests to avoid SDK version drift.
    """
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY not set")

    url = f"{OPENAI_API_BASE}/chat/completions"
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    resp = requests.post(url, json=payload, headers=headers, timeout=60)
    if resp.status_code >= 400:
        raise RuntimeError(f"OpenAI error {resp.status_code}: {resp.text}")
    data = resp.json()
    return data["choices"][0]["message"]["content"].strip()


def _format_sources(papers: List[Dict[str, Any]], max_chars: int = 5500) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Build a compact context block and a clean list of citeable sources.
    """
    ctx_lines = []
    cites: List[Dict[str, Any]] = []
    total = 0
    for i, p in enumerate(papers, start=1):
        title = p.get("title") or "Untitled"
        year  = p.get("year") or "n/a"
        url   = p.get("url")  or ""
        abstract = (p.get("abstract") or p.get("summary") or "").strip()
        snippet = abstract[:800]
        entry = f"[{i}] {title} ({year})\nURL: {url}\nAbstract: {snippet}\n"
        if total + len(entry) > max_chars:
            break
        ctx_lines.append(entry)
        cites.append({"idx": i, "title": title, "url": url, "year": year})
        total += len(entry)
    return "\n".join(ctx_lines), cites


def answer_with_rag(query: str, search_fn: Callable[[str, int], List[Dict[str, Any]]], model: str = "gpt-4o-mini") -> Tuple[str, List[Dict[str, Any]]]:
    """
    Given a query and a search function that returns top-k paper dicts,
    format a prompt and call OpenAI to produce a grounded answer.
    """
    top = search_fn(query, 6) or []
    context, sources = _format_sources(top)

    system = (
        "You are an expert assistant for NASA Space Biology. "
        "Answer concisely and factually using ONLY the provided sources. "
        "If unsure, say you are unsure. Include specific findings, organisms, missions, "
        "and note any limitations or disagreements across studies."
    )
    user = textwrap.dedent(f"""
        User question:
        {query}

        Sources:
        {context}

        Instructions:
        - Cite sources inline using [#] like [1], [2].
        - Start with a 1–2 sentence answer, then give 3–7 bullet points of key findings or gaps.
        - If relevant, separate sections for Humans / Plants / Microbes.
    """).strip()

    content = _post_chat(
        messages=[{"role": "system", "content": system},
                  {"role": "user", "content": user}],
        model=model,
        temperature=0.2
    )
    return content, sources


def summarize_text(text: str, style: str = "keypoints", model: str = "gpt-4o-mini") -> str:
    """
    Summarize a single paper section or abstract.
    style: keypoints | abstract | methods | results | conclusion
    """
    style_map = {
        "keypoints": "Return 5-8 bullet key results with numbers where possible.",
        "abstract":  "Rewrite a crisp 4-6 sentence abstract for a general technical audience.",
        "methods":   "Summarize methods, including organisms, environment (e.g., ISS, microgravity), and measurement endpoints.",
        "results":   "Summarize the objectively demonstrated results only. Avoid speculation.",
        "conclusion":"Summarize forward-looking implications, limitations, and open questions.",
    }
    instruction = style_map.get(style, style_map["keypoints"])

    system = "You are an excellent scientific editor. Be precise, faithful, and concise."
    user = textwrap.dedent(f"""
        Summarize the following text for NASA Space Biology readers.

        Style: {instruction}

        Text:
        {text}
    """).strip()

    return _post_chat(
        messages=[{"role": "system", "content": system},
                  {"role": "user", "content": user}],
        model=model,
        temperature=0.2
    )
