#!/usr/bin/env python3
"""
Database setup and management for the Space Bio Engine
"""

import sqlite3
import csv
import os
from typing import List, Dict, Optional

DATABASE_PATH = "data/papers.db"

def create_database():
    """Create the database and tables"""
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Create papers table with all necessary fields
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS papers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            organism TEXT,
            year INTEGER,
            source TEXT,
            authors TEXT,
            mission TEXT,
            environment TEXT,
            summary TEXT,
            citations INTEGER DEFAULT 0,
            hasOSDR BOOLEAN DEFAULT 0,
            hasDOI BOOLEAN DEFAULT 0,
            bookmarked BOOLEAN DEFAULT 0,
            abstract TEXT,
            keyResults TEXT,  -- JSON array as string
            methods TEXT,
            conclusions TEXT,
            doi TEXT,
            osdrLink TEXT,
            taskBookLink TEXT,
            pdf_url TEXT,
            pmcid TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create index for faster searches
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_title ON papers(title)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_year ON papers(year)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_organism ON papers(organism)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_source ON papers(source)')
    
    conn.commit()
    conn.close()
    print(f"✅ Database created at {DATABASE_PATH}")

def migrate_csv_to_database(csv_path: str):
    """Migrate data from CSV to database"""
    if not os.path.exists(csv_path):
        print(f"❌ CSV file not found: {csv_path}")
        return
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Clear existing data
    cursor.execute('DELETE FROM papers')
    
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        print(f"📄 CSV columns: {reader.fieldnames}")
        
        i = 1
        row_count = 0
        for row in reader:
            row_count += 1
            
            # Handle different column name variations (including BOM)
            title = (row.get("title") or row.get("Title") or row.get("\ufeffTitle") or row.get("name") or "").strip()
            url = (row.get("url") or row.get("Link") or row.get("link") or "").strip()
            
            # Optional fields if present
            organism = (row.get("organism") or row.get("Organism") or "").strip()
            year = (row.get("year") or row.get("Year") or "").strip()
            source = (row.get("source") or row.get("Source") or "").strip()
            
            if title and url:
                # Insert paper with default values for enriched fields
                cursor.execute('''
                    INSERT INTO papers (
                        title, url, organism, year, source,
                        authors, mission, environment, summary, citations,
                        hasOSDR, hasDOI, bookmarked, abstract, keyResults,
                        methods, conclusions, doi, osdrLink, taskBookLink
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    title, url,
                    organism or None,
                    int(year) if year.isdigit() else 2023,
                    source or None,
                    "Unknown Author",  # Default values for enriched fields
                    "Unknown Mission",
                    "Space Environment", 
                    title[:100] + "..." if len(title) > 100 else title,
                    0,  # citations
                    False,  # hasOSDR
                    False,  # hasDOI
                    False,  # bookmarked
                    title,  # abstract (initially just title)
                    "[]",  # keyResults as empty JSON array
                    "Not specified",  # methods
                    "Not specified",  # conclusions
                    "",  # doi
                    "",  # osdrLink
                    ""   # taskBookLink
                ))
                i += 1
        
        print(f"📊 Total rows processed: {row_count}")
        print(f"✅ Valid papers inserted: {i-1}")
    
    conn.commit()
    conn.close()

def get_paper_by_id(paper_id: int) -> Optional[Dict]:
    """Get a single paper by ID"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM papers WHERE id = ?', (paper_id,))
    row = cursor.fetchone()
    
    conn.close()
    
    if row:
        return dict(row)
    return None

def get_papers(limit: int = 50, offset: int = 0) -> List[Dict]:
    """Get papers with pagination"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM papers ORDER BY id LIMIT ? OFFSET ?', (limit, offset))
    rows = cursor.fetchall()
    
    conn.close()
    
    return [dict(row) for row in rows]

def search_papers(query: str, limit: int = 50) -> List[Dict]:
    """Search papers by title"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM papers 
        WHERE title LIKE ? 
        ORDER BY id 
        LIMIT ?
    ''', (f'%{query}%', limit))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def update_paper_enrichment(paper_id: int, enrichment_data: Dict):
    """Update a paper with enriched data from PMC parsing"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Convert keyResults list to JSON string
    key_results_json = "[]"
    if enrichment_data.get("keyResults"):
        import json
        key_results_json = json.dumps(enrichment_data["keyResults"])
    
    cursor.execute('''
        UPDATE papers SET
            title = COALESCE(?, title),
            authors = COALESCE(?, authors),
            year = COALESCE(?, year),
            doi = COALESCE(?, doi),
            abstract = COALESCE(?, abstract),
            pdf_url = COALESCE(?, pdf_url),
            pmcid = COALESCE(?, pmcid),
            source = COALESCE(?, source),
            hasDOI = ?,
            taskBookLink = COALESCE(?, taskBookLink),
            summary = COALESCE(?, summary),
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (
        enrichment_data.get("title"),
        enrichment_data.get("authors"),
        enrichment_data.get("year"),
        enrichment_data.get("doi"),
        enrichment_data.get("abstract"),
        enrichment_data.get("pdf_url"),
        enrichment_data.get("pmcid"),
        enrichment_data.get("source"),
        bool(enrichment_data.get("doi")),
        enrichment_data.get("pdf_url"),
        enrichment_data.get("abstract", "")[:200] + "..." if enrichment_data.get("abstract") and len(enrichment_data.get("abstract", "")) > 200 else enrichment_data.get("abstract"),
        paper_id
    ))
    
    conn.commit()
    conn.close()

def get_papers_count() -> int:
    """Get total number of papers"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM papers')
    count = cursor.fetchone()[0]
    
    conn.close()
    return count

def get_pmc_papers_to_enrich() -> List[Dict]:
    """Get papers that are PMC URLs and need enrichment"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM papers 
        WHERE (url LIKE '%pmc.ncbi.nlm.nih.gov%' OR url LIKE '%ncbi.nlm.nih.gov/pmc%')
        AND (abstract IS NULL OR length(abstract) < 100 OR authors = 'Unknown Author')
        ORDER BY id
    ''')
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

if __name__ == "__main__":
    # Setup database and migrate CSV data
    create_database()
    migrate_csv_to_database("data/papers.csv")
    print(f"📊 Total papers in database: {get_papers_count()}")
