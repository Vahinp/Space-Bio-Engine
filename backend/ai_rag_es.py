# ai_rag_es.py
# -*- coding: utf-8 -*-
"""
LangChain RAG over scraped_results.csv using Elasticsearch as the vector store.
- Creates/uses an ES index with a dense_vector field for embeddings
- Supports pure vector or hybrid retrieval (BM25 + vector)
"""

import os
import json
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple

from langchain.schema import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import ElasticsearchStore
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever

from langchain.prompts import PromptTemplate
from langchain.chains.qa_with_sources.loading import load_qa_with_sources_chain
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.language_models import BaseLanguageModel


# --------- Globals ----------
_RETRIEVER = None
_LLM: Optional[BaseLanguageModel] = None
_INIT_DONE = False
_DOCS_CACHE: List[Document] = []  # used for BM25/hybrid

def _build_docs_from_csv(csv_path: str) -> List[Document]:
    df = pd.read_csv(csv_path).fillna("")
    docs: List[Document] = []
    for _, r in df.iterrows():
        abstract = (r.get("abstract") or "").strip()
        if not abstract:
            continue
        meta = {
            "id": str(r.get("id", "")),
            "title": str(r.get("title", "")),
            "url": str(r.get("url", "")),
            "year": int(r.get("year")) if str(r.get("year")).isdigit() else None,
            "source": str(r.get("source", "")),
            "doi": str(r.get("doi", "")),
        }
        docs.append(Document(page_content=abstract, metadata=meta))
    return docs

def _make_llm() -> Optional[BaseLanguageModel]:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp").strip()
    if not api_key:
        return None
    return ChatGoogleGenerativeAI(
        model=model,
        google_api_key=api_key,
        temperature=0.1,
        max_output_tokens=1024,
    )

def _format_sources(docs: List[Document]) -> List[Dict[str, Any]]:
    out = []
    for i, d in enumerate(docs, 1):
        m = d.metadata or {}
        out.append({
            "idx": i,
            "title": m.get("title") or "(untitled)",
            "url": m.get("url") or "",
            "year": m.get("year"),
            "source": m.get("source"),
            "doi": m.get("doi"),
            "snippet": d.page_content[:250] + ("..." if len(d.page_content) > 250 else "")
        })
    return out

def init_rag(
    csv_path: str = "data/scraped_results.csv",
    index_name: str = None,
    es_url: str = None,
    es_user: str = None,
    es_password: str = None,
    use_hybrid: bool = True,
    k: int = 6,
) -> None:
    """
    Initialize ES vector store and retriever.
    Environment fallbacks:
      ES_URL, ES_USER, ES_PASSWORD, ES_INDEX_NAME
    """
    global _RETRIEVER, _LLM, _INIT_DONE, _DOCS_CACHE
    if _INIT_DONE:
        return

    index_name = index_name or os.getenv("ES_INDEX_NAME", "space_bio_vectors")
    es_url = es_url or os.getenv("ES_URL", "http://localhost:9200")
    es_user = es_user or os.getenv("ES_USERNAME", "elastic")
    es_password = es_password or os.getenv("ES_PASSWORD", "changeme")

    # 384 dims for all-MiniLM-L6-v2
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    # Build/load documents
    docs = _build_docs_from_csv(csv_path)
    if not docs:
        raise RuntimeError("No documents with abstracts found in CSV.")
    _DOCS_CACHE = docs  # for BM25 hybrid

    # Create or connect the ES vector index and upsert docs
    # NOTE: from_documents() will create the index with appropriate mapping (dense_vector)
    vstore = ElasticsearchStore.from_documents(
        documents=docs,
        embedding=embeddings,
        es_url=es_url,
        index_name=index_name,
        http_auth=(es_user, es_password),
        # You can also set strategy params in newer LC versions if you need IVF/HNSW specifics
    )

    vector_retriever = vstore.as_retriever(search_kwargs={"k": k})

    if use_hybrid:
        # Add a BM25 retriever over the same docs for classic lexical matching
        bm25 = BM25Retriever.from_documents(docs)
        bm25.k = k
        _RETRIEVER = EnsembleRetriever(
            retrievers=[bm25, vector_retriever],
            weights=[0.4, 0.6],  # favor semantic a bit
        )
    else:
        _RETRIEVER = vector_retriever

    _LLM = _make_llm()
    _INIT_DONE = True
    print(f"✅ RAG (Elasticsearch) initialized: index='{index_name}', hybrid={use_hybrid}, k={k}")

def _build_chain():
    if _LLM is None or _RETRIEVER is None:
        return None
    prompt = PromptTemplate.from_template(
        """You are a NASA space biology assistant. Answer strictly using the provided context.
If the answer is not in the context, say you don’t know.

Question:
{question}

Context (abstract snippets):
{context}

Answer (be concise, with citations in [#] referencing the sources list):"""
    )
    return load_qa_with_sources_chain(_LLM, chain_type="stuff", prompt=prompt)

def answer_with_rag(query: str, k: int = 5, **_) -> Tuple[str, List[Dict[str, Any]]]:
    if not _INIT_DONE:
        init_rag(
            csv_path=os.getenv("CSV_PATH", "data/scraped_results.csv"),
            index_name=os.getenv("ES_INDEX_NAME", "space_bio_vectors"),
            es_url=os.getenv("ES_URL", "http://localhost:9200"),
            es_user=os.getenv("ES_USERNAME", "elastic"),
            es_password=os.getenv("ES_PASSWORD", "changeme"),
            use_hybrid=bool(os.getenv("RAG_HYBRID", "1") != "0"),
            k=int(os.getenv("RAG_TOPK", "6")),
        )

    retrieved = _RETRIEVER.get_relevant_documents(query)[:k]
    sources = _format_sources(retrieved)

    if _LLM is None:
        bullets = [f"- [{i}] {(d.metadata.get('title') or 'Source')}: {d.page_content[:220].strip()}..."
                   for i, d in enumerate(retrieved, 1)]
        answer = "Here’s what I found in the abstracts (LLM-free mode):\n" + "\n".join(bullets)
        return answer, sources

    chain = _build_chain()
    context = "\n\n---\n\n".join([d.page_content for d in retrieved])
    result = chain.invoke({"question": query, "input_documents": retrieved, "context": context})
    answer = result.get("output_text") or result.get("output") or ""
    if not answer:
        answer = "I couldn't find enough evidence in the abstracts to answer confidently."
    return answer, sources

def summarize_text(text: str, style: str = "keypoints", model: Optional[str] = None) -> str:
    if not text.strip():
        return ""
    if _LLM is None:
        return "\n".join(f"- {line.strip()}" for line in text.split(".") if line.strip())[:1200]
    prompt = (
        "Summarize the following text from a space biology abstract. "
        f"Style: {style}.\n\nText:\n{text}\n\nSummary:"
    )
    resp = _LLM.invoke(prompt)
    return getattr(resp, "content", None) or str(resp)
