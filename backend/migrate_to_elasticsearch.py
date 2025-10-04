#!/usr/bin/env python3
"""
Migrate data from SQLite database to Elasticsearch
"""

import os
import sys
from database import get_all_papers_from_db
from elasticsearch_service import es_service
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
