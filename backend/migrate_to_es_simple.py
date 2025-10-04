#!/usr/bin/env python3
"""
Simple migration script to move papers from SQLite to Elasticsearch
"""

import os
import json
import requests
from database import get_papers

# Elasticsearch configuration
ES_ENDPOINT = "http://localhost:9200"
ES_USERNAME = "elastic"
ES_PASSWORD = "elasSer12!"
INDEX_NAME = "space_bio_papers"

def index_paper(paper):
    """Index a single paper to Elasticsearch"""
    # Convert paper to Elasticsearch format
    es_paper = {
        "paper_id": str(paper['id']),
        "title": paper['title'],
        "abstract": paper['abstract'],
        "authors": paper['authors'],
        "venue": paper['source'] or 'Unknown',
        "date": f"{paper['year']}-01-01",
        "year": paper['year'],
        "url": paper['url'],
        "doi": paper['doi'],
        "organism": paper['organism'] or 'Unknown',
        "mission": paper['mission'],
        "environment": paper['environment'],
        "citations": paper['citations'],
        "hasOSDR": bool(paper['hasOSDR']),
        "hasDOI": bool(paper['hasDOI'])
    }
    
    # Index the document
    url = f"{ES_ENDPOINT}/{INDEX_NAME}/_doc/{es_paper['paper_id']}"
    response = requests.put(
        url,
        auth=(ES_USERNAME, ES_PASSWORD),
        headers={'Content-Type': 'application/json'},
        data=json.dumps(es_paper)
    )
    
    if response.status_code in [200, 201]:
        print(f"✅ Indexed: {paper['title'][:50]}...")
        return True
    else:
        print(f"❌ Failed: {paper['title'][:50]}... - {response.text}")
        return False

def main():
    print("🚀 Starting migration of all papers to Elasticsearch...")
    
    # Get all papers
    papers = get_papers(limit=1000, offset=0)
    print(f"📊 Found {len(papers)} papers in database")
    
    # Index papers
    success_count = 0
    error_count = 0
    
    for i, paper in enumerate(papers):
        print(f"📦 Processing {i+1}/{len(papers)}...")
        if index_paper(paper):
            success_count += 1
        else:
            error_count += 1
    
    print(f"\n✅ Migration complete!")
    print(f"📊 Successfully indexed: {success_count}")
    print(f"❌ Errors: {error_count}")
    
    # Test search
    print("\n🔍 Testing search...")
    search_url = f"{ES_ENDPOINT}/{INDEX_NAME}/_search"
    search_query = {
        "size": 5,
        "query": {
            "multi_match": {
                "query": "microgravity",
                "fields": ["title^3", "abstract"]
            }
        }
    }
    
    response = requests.post(
        search_url,
        auth=(ES_USERNAME, ES_PASSWORD),
        headers={'Content-Type': 'application/json'},
        data=json.dumps(search_query)
    )
    
    if response.status_code == 200:
        data = response.json()
        total = data['hits']['total']['value']
        print(f"🔍 Search test: {total} results found for 'microgravity'")
    else:
        print(f"❌ Search test failed: {response.text}")

if __name__ == "__main__":
    main()
