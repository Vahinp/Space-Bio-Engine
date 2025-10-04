#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scrape title, publish date, and abstract from URLs listed in a CSV (2nd column).
Usage:
  python scrape_from_csv.py --in links.csv --out scraped_results.csv
Options:
  --no-header        Treat the first row as data (no header).
  --sleep 0.5        Seconds between requests (default: 0.5)
  --no-crossref      Disable DOI->Crossref fallback
"""
import argparse, csv, json, re, time
from typing import Optional, List, Tuple, Dict
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from dateutil import parser as dateparser

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; paper-meta-scraper/1.0)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

META_TITLE_KEYS = ["citation_title", "og:title", "twitter:title", "dc.title", "DC.Title", "title"]
META_DATE_KEYS = [
    "citation_publication_date","citation_date",
    "dc.date","dc.date.issued","DC.Date","DC.Date.issued",
    "prism.publicationdate","prism.publicationDate",
    "article:published_time","og:published_time",
    "date","publish_date","publication_date","pubdate"
]
META_ABSTRACT_KEYS = [
    "citation_abstract", "dc.description", "DC.Description",
    "og:description", "twitter:description", "description", "abstract"
]
DOI_META_KEYS = ["citation_doi","dc.identifier","dc.identifier.doi","doi"]
DOI_REGEX = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b", re.I)

def robust_get(url: str, timeout: float = 20, tries: int = 3, backoff: float = 1.5):
    for i in range(tries):
        try:
            resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
            if 200 <= resp.status_code < 400:
                return resp
        except Exception:
            pass
        time.sleep(backoff ** i)
    return None

def find_meta_content(soup: BeautifulSoup, key: str):
    tag = soup.find("meta", attrs={"name": re.compile(f"^{re.escape(key)}$", re.I)})
    if tag and tag.get("content"):
        return tag["content"].strip()
    tag = soup.find("meta", attrs={"property": re.compile(f"^{re.escape(key)}$", re.I)})
    if tag and tag.get("content"):
        return tag["content"].strip()
    return None

def extract_jsonld(soup: BeautifulSoup):
    blobs = []
    for script in soup.find_all("script", {"type": "application/ld+json"}):
        try:
            data = json.loads(script.string or "")
            blobs.extend(data if isinstance(data, list) else [data])
        except Exception:
            continue
    return [b for b in blobs if isinstance(b, dict)]

def extract_title(soup: BeautifulSoup):
    for key in META_TITLE_KEYS:
        v = find_meta_content(soup, key)
        if v:
            return v
    for obj in extract_jsonld(soup):
        for k in ("headline", "name", "title"):
            v = obj.get(k)
            if isinstance(v, str) and v.strip():
                return v.strip()
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    return None

def parse_any_date(s: str):
    try:
        return dateparser.parse(s, fuzzy=True, default=datetime(1900,1,1))
    except Exception:
        return None

def extract_date(soup: BeautifulSoup, html_text: str, url: str):
    candidates = []
    for key in META_DATE_KEYS:
        v = find_meta_content(soup, key)
        if v:
            candidates.append(v)
    for obj in extract_jsonld(soup):
        for k in ("datePublished","dateCreated","dateModified","dateIssued"):
            v = obj.get(k)
            if isinstance(v, str):
                candidates.append(v.strip())
    parsed = [p for p in (parse_any_date(c) for c in candidates) if p]
    if parsed:
        parsed.sort()
        dt = next((p for p in parsed if p.year >= 1900), parsed[0])
        return dt.date().isoformat(), dt.year, "html/json-ld"
    return None, None, ""

def extract_doi(soup: BeautifulSoup, html_text: str, url: str):
    for key in DOI_META_KEYS:
        v = find_meta_content(soup, key)
        if v:
            m = DOI_REGEX.search(v)
            if m:
                return m.group(0)
    for obj in extract_jsonld(soup):
        ident = obj.get("identifier")
        if isinstance(ident, str):
            m = DOI_REGEX.search(ident)
            if m:
                return m.group(0)
        elif isinstance(ident, dict):
            m = DOI_REGEX.search(json.dumps(ident))
            if m:
                return m.group(0)
    m = DOI_REGEX.search(html_text) or DOI_REGEX.search(url)
    return m.group(0) if m else None

def clean_text(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()

def extract_abstract(soup: BeautifulSoup):
    for key in META_ABSTRACT_KEYS:
        v = find_meta_content(soup, key)
        if v and len(v.strip()) > 30:
            return clean_text(v)
    abstract_selectors = [
        ('section', {'id': re.compile("abstract", re.I)}),
        ('section', {'class': re.compile("abstract", re.I)}),
        ('div', {'id': re.compile("abstract", re.I)}),
        ('div', {'class': re.compile("abstract", re.I)}),
        ('p', {'class': re.compile("abstract", re.I)}),
        ('article', {'class': re.compile("abstract", re.I)}),
    ]
    for tag, attrs in abstract_selectors:
        el = soup.find(tag, attrs=attrs)
        if el:
            text = clean_text(el.get_text(" ", strip=True))
            if len(text) > 30:
                return text
    blk = soup.find("blockquote", {"class": re.compile("abstract", re.I)})
    if blk:
        text = clean_text(blk.get_text(" ", strip=True).replace("Abstract:", "").strip())
        if len(text) > 30:
            return text
    return None

def crossref_fetch(doi: str, timeout: float = 20):
    try:
        url = f"https://api.crossref.org/works/{requests.utils.quote(doi)}"
        r = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
        if r.status_code != 200:
            return None, None, None
        msg = r.json().get("message", {})
        def datepart(obj):
            if not isinstance(obj, dict):
                return None
            parts = obj.get("date-parts")
            if isinstance(parts, list) and parts and isinstance(parts[0], list):
                ymd = parts[0] + [1,1]
                try:
                    return datetime(int(ymd[0]), int(ymd[1]), int(ymd[2]))
                except Exception:
                    return None
            return None
        dt = None
        for key in ["issued","created","published-print","published-online","deposited"]:
            dt = datepart(msg.get(key)) or dt
        date_iso, year = (dt.date().isoformat(), dt.year) if dt else (None, None)
        abstract = msg.get("abstract")
        if isinstance(abstract, str):
            abstract = re.sub(r"<[^>]+>", " ", abstract)
            abstract = clean_text(abstract)
        return date_iso, year, abstract
    except Exception:
        return None, None, None

def process_url(url: str, allow_crossref: bool = True, timeout: float = 20):
    rec = {"url": url, "title": None, "date_iso": None, "year": None, "abstract": None, "source": None, "doi": None, "notes": []}
    resp = robust_get(url, timeout=timeout)
    if not resp:
        rec["notes"].append("fetch_failed")
        return rec
    html = resp.text
    soup = BeautifulSoup(html, "html.parser")

    title = extract_title(soup)
    if title:
        rec["title"] = title

    date_iso, year, src = extract_date(soup, html, url)
    if not date_iso:
        lm = resp.headers.get("Last-Modified")
        if lm:
            try:
                dt = dateparser.parse(lm, fuzzy=True)
                if dt:
                    date_iso, year, src = dt.date().isoformat(), dt.year, "http_last_modified"
            except Exception:
                pass
    if date_iso:
        rec["date_iso"] = date_iso
        rec["year"] = year
        rec["source"] = src

    abstract = extract_abstract(soup)
    if abstract:
        rec["abstract"] = abstract

    doi = extract_doi(soup, html, url)
    if doi:
        rec["doi"] = doi
        if allow_crossref and (not rec["date_iso"] or not rec["abstract"]):
            cr_date_iso, cr_year, cr_abs = crossref_fetch(doi, timeout=timeout)
            if cr_date_iso and not rec["date_iso"]:
                rec["date_iso"] = cr_date_iso
                rec["year"] = cr_year
                rec["source"] = "crossref"
            if cr_abs and (not rec["abstract"] or len(rec["abstract"]) < 40):
                rec["abstract"] = cr_abs
    return rec

def looks_like_url(s: str) -> bool:
    return s.startswith("http://") or s.startswith("https://") or s.startswith("doi.org/") or s.startswith("10.")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="in_csv", required=True, help="Input CSV where 2nd column is URL")
    ap.add_argument("--out", dest="out_csv", default="scraped_results.csv", help="Output CSV")
    ap.add_argument("--no-header", action="store_true", help="Treat first row as data (no header)")
    ap.add_argument("--sleep", type=float, default=0.5, help="Seconds to sleep between requests")
    ap.add_argument("--no-crossref", action="store_true", help="Disable DOI->Crossref fallback")
    args = ap.parse_args()

    rows = []
    with open(args.in_csv, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        for idx, row in enumerate(reader):
            if not row or len(row) < 2:
                continue
            if idx == 0 and not args.no_header:
                continue  # skip header
            url = row[1].strip()
            if not url:
                continue
            rec = process_url(url, allow_crossref=(not args.no_crossref))
            rec["id"] = idx if args.no_header else idx
            rows.append(rec)
            print(f"[{len(rows)}] {url} -> title='{(rec['title'] or '')[:80]}', date={rec['date_iso']}, hasAbs={bool(rec['abstract'])}")
            time.sleep(args.sleep)

    fieldnames = ["id","title","url","date_iso","year","abstract","source","doi","notes"]
    with open(args.out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            r2 = r.copy()
            if isinstance(r2.get("notes"), list):
                r2["notes"] = ";".join(r2["notes"])
            w.writerow(r2)

    print(f"[ok] wrote {len(rows)} rows to {args.out_csv}")

if __name__ == "__main__":
    main()
