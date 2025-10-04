#!/usr/bin/env python3
"""
Update database with new papers from CSV and enrich them
"""

import os
import sqlite3
import csv
import json
from pmc_scrape import parse_pmc_article
import time

def get_existing_paper_urls():
    """Get all existing paper URLs from database"""
    conn = sqlite3.connect('data/papers.db')
    cursor = conn.cursor()
    cursor.execute('SELECT url FROM papers')
    existing_urls = set(row[0] for row in cursor.fetchall())
    conn.close()
    return existing_urls

def load_papers_from_csv(csv_path):
    """Load papers from CSV file"""
    papers = []
    with open(csv_path, 'r', encoding='utf-8') as file:
        # Handle BOM character
        content = file.read()
        if content.startswith('\ufeff'):
            content = content[1:]
        
        reader = csv.DictReader(content.splitlines())
        for row in reader:
            if row.get('Title') and row.get('Link'):
                papers.append({
                    'title': row['Title'].strip(),
                    'url': row['Link'].strip()
                })
    return papers

def add_paper_to_database(paper_data):
    """Add a single paper to the database"""
    conn = sqlite3.connect('data/papers.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO papers (title, url, organism, year, source, authors, mission, environment, summary, citations, hasOSDR, hasDOI, bookmarked, abstract, keyResults, methods, conclusions, doi, osdrLink, taskBookLink)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            paper_data["title"], paper_data["url"], paper_data["organism"], 
            paper_data["year"], paper_data["source"], paper_data["authors"], paper_data["mission"], 
            paper_data["environment"], paper_data["summary"], paper_data["citations"], 
            paper_data["hasOSDR"], paper_data["hasDOI"], paper_data["bookmarked"], 
            paper_data["abstract"], paper_data["keyResults"], paper_data["methods"], 
            paper_data["conclusions"], paper_data["doi"], paper_data["osdrLink"], 
            paper_data["taskBookLink"]
        ))
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        print(f"Error adding paper: {e}")
        return None
    finally:
        conn.close()

def enrich_paper(paper_id, url):
    """Enrich a paper with PMC data"""
    try:
        print(f"Enriching paper {paper_id}: {url}")
        result = parse_pmc_article(url)
        
        if result.get('error'):
            print(f"  ❌ Error: {result.get('error')}")
            return False
        
        # Update the paper in database
        conn = sqlite3.connect('data/papers.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE papers SET
                title = ?, authors = ?, year = ?, abstract = ?, doi = ?, taskBookLink = ?
            WHERE id = ?
        """, (
            result.get('title', ''),
            result.get('authors', 'Unknown Author'),
            result.get('year', 2023),
            result.get('abstract', ''),
            result.get('doi', ''),
            result.get('pdf_url', ''),
            paper_id
        ))
        
        conn.commit()
        conn.close()
        
        print(f"  ✅ Enriched: {result.get('title', 'Unknown')[:50]}...")
        return True
        
    except Exception as e:
        print(f"  ❌ Exception: {str(e)}")
        return False

def main():
    print("🔄 Updating database with new papers...")
    
    # Load papers from CSV
    csv_papers = load_papers_from_csv('data/papers.csv')
    print(f"📄 Loaded {len(csv_papers)} papers from CSV")
    
    # Get existing URLs
    existing_urls = get_existing_paper_urls()
    print(f"🗄️ Database has {len(existing_urls)} existing papers")
    
    # Find new papers
    new_papers = []
    for paper in csv_papers:
        if paper['url'] not in existing_urls:
            new_papers.append(paper)
    
    print(f"🆕 Found {len(new_papers)} new papers to add")
    
    if not new_papers:
        print("✅ No new papers to add!")
        return
    
    # Add new papers to database
    added_papers = []
    for i, paper in enumerate(new_papers):
        print(f"Adding paper {i+1}/{len(new_papers)}: {paper['title'][:50]}...")
        
        # Create basic paper data
        paper_data = {
            "title": paper['title'],
            "url": paper['url'],
            "organism": "Unknown",
            "year": 2023,
            "source": "PMC",
            "authors": "Unknown Author",
            "mission": "Unknown Mission",
            "environment": "Space Environment",
            "summary": "",
            "citations": 0,
            "hasOSDR": False,
            "hasDOI": False,
            "bookmarked": False,
            "abstract": "",
            "keyResults": "[]",
            "methods": "Not specified",
            "conclusions": "Not specified",
            "doi": "",
            "osdrLink": "",
            "taskBookLink": ""
        }
        
        paper_id = add_paper_to_database(paper_data)
        if paper_id:
            added_papers.append((paper_id, paper['url']))
            print(f"  ✅ Added with ID {paper_id}")
        else:
            print(f"  ❌ Failed to add")
    
    print(f"\n📊 Added {len(added_papers)} new papers to database")
    
    # Enrich the new papers
    if added_papers:
        print(f"\n🔬 Enriching {len(added_papers)} new papers...")
        enriched_count = 0
        error_count = 0
        
        for i, (paper_id, url) in enumerate(added_papers):
            print(f"\nEnriching {i+1}/{len(added_papers)}...")
            if enrich_paper(paper_id, url):
                enriched_count += 1
            else:
                error_count += 1
            
            # Small delay to be respectful
            time.sleep(0.5)
        
        print(f"\n✅ Enrichment complete!")
        print(f"📊 Successfully enriched: {enriched_count}")
        print(f"❌ Errors: {error_count}")
    
    # Update Elasticsearch
    print(f"\n🔄 Updating Elasticsearch...")
    try:
        from migrate_to_elasticsearch import migrate_papers_to_elasticsearch
        migrate_papers_to_elasticsearch()
        print("✅ Elasticsearch updated!")
    except Exception as e:
        print(f"❌ Error updating Elasticsearch: {e}")
    
    print(f"\n🎉 Database update complete!")

if __name__ == "__main__":
    main()
