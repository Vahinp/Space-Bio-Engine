#!/usr/bin/env python3
"""
Migrate data from SQLite database to Elasticsearch
"""

import os
import sys
import sqlite3
from elasticsearch_service import es_service
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_all_papers_from_db():
    """Get all papers from the database"""
    conn = sqlite3.connect('data/papers.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, title, url, organism, year, source, authors, mission, environment, 
               abstract, citations, hasOSDR, hasDOI, doi, osdrLink, taskBookLink
        FROM papers
        ORDER BY id
    """)
    
    papers = []
    for row in cursor.fetchall():
        # Clean year data - handle invalid years
        year = row[4]
        if year and (isinstance(year, int) and 1900 <= year <= 2030):
            clean_year = year
        else:
            clean_year = 2023  # Default year
        
        papers.append({
            "id": row[0],
            "title": row[1],
            "url": row[2],
            "organism": row[3],
            "year": clean_year,
            "source": row[5],
            "authors": row[6],
            "mission": row[7],
            "environment": row[8],
            "abstract": row[9],
            "citations": row[10],
            "hasOSDR": bool(row[11]) if row[11] is not None else False,
            "hasDOI": bool(row[12]) if row[12] is not None else False,
            "doi": row[13],
            "osdrLink": row[14],
            "taskBookLink": row[15]
        })
    
    conn.close()
    return papers

def migrate_data():
    """Migrate all papers from database to Elasticsearch"""
    try:
        logger.info("🚀 Starting data migration to Elasticsearch...")
        
        # Get all papers from database
        papers = get_all_papers_from_db()
        logger.info(f"📊 Found {len(papers)} papers in database")
        
        if not papers:
            logger.warning("⚠️ No papers found in database")
            return
        
        # Index papers in batches
        batch_size = 100
        total_indexed = 0
        total_errors = 0
        
        for i in range(0, len(papers), batch_size):
            batch = papers[i:i + batch_size]
            logger.info(f"📦 Processing batch {i//batch_size + 1}/{(len(papers) + batch_size - 1)//batch_size}")
            
            result = es_service.bulk_index_papers(batch)
            total_indexed += result["success"]
            total_errors += result["errors"]
            
            logger.info(f"✅ Batch complete: {result['success']} indexed, {result['errors']} errors")
        
        logger.info(f"🎉 Migration complete!")
        logger.info(f"📊 Total indexed: {total_indexed}")
        logger.info(f"❌ Total errors: {total_errors}")
        
        # Test search
        logger.info("🔍 Testing search...")
        search_result = es_service.search_papers(query="microgravity", size=5)
        logger.info(f"📈 Search test: {search_result['total']} results found")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    migrate_data()
