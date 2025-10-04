#!/usr/bin/env python3
"""
Import papers from scraped_results.csv to database
"""

import os
import sqlite3
import csv
import json
from datetime import datetime

def get_existing_paper_urls():
    """Get all existing paper URLs from database"""
    conn = sqlite3.connect('data/papers.db')
    cursor = conn.cursor()
    cursor.execute('SELECT url FROM papers')
    existing_urls = set(row[0] for row in cursor.fetchall())
    conn.close()
    return existing_urls

def load_scraped_papers(csv_path):
    """Load papers from scraped_results.csv file"""
    papers = []
    with open(csv_path, 'r', encoding='utf-8') as file:
        # Handle BOM character
        content = file.read()
        if content.startswith('\ufeff'):
            content = content[1:]
        
        reader = csv.DictReader(content.splitlines())
        for row in reader:
            if row.get('title') and row.get('url'):
                # Parse year as integer
                year = None
                if row.get('year'):
                    try:
                        year = int(row['year'])
                    except (ValueError, TypeError):
                        year = 2023  # Default year
                
                # Parse date_iso if available
                date_iso = row.get('date_iso', '')
                
                papers.append({
                    'id': row.get('id', ''),
                    'title': row['title'].strip(),
                    'url': row['url'].strip(),
                    'date_iso': date_iso,
                    'year': year,
                    'abstract': row.get('abstract', '').strip(),
                    'source': row.get('source', 'Unknown'),
                    'doi': row.get('doi', '').strip(),
                    'notes': row.get('notes', '').strip()
                })
    return papers

def add_paper_to_database(paper_data):
    """Add a single paper to the database"""
    conn = sqlite3.connect('data/papers.db')
    cursor = conn.cursor()
    
    try:
        # Extract authors from title or use default
        authors = "Unknown Author"
        if paper_data.get('notes'):
            authors = paper_data['notes']
        
        # Determine organism based on title keywords
        organism = "Unknown"
        title_lower = paper_data['title'].lower()
        if any(keyword in title_lower for keyword in ['mouse', 'mice', 'murine']):
            organism = "Mouse"
        elif any(keyword in title_lower for keyword in ['human', 'astronaut', 'crew']):
            organism = "Human"
        elif any(keyword in title_lower for keyword in ['plant', 'arabidopsis', 'lettuce', 'wheat']):
            organism = "Plant"
        elif any(keyword in title_lower for keyword in ['bacteria', 'microbe', 'microbial']):
            organism = "Microbe"
        elif any(keyword in title_lower for keyword in ['rat', 'rodent']):
            organism = "Rat"
        elif any(keyword in title_lower for keyword in ['drosophila', 'fly']):
            organism = "Drosophila"
        elif any(keyword in title_lower for keyword in ['c. elegans', 'nematode']):
            organism = "C. elegans"
        
        # Determine mission based on title keywords
        mission = "Unknown Mission"
        if any(keyword in title_lower for keyword in ['iss', 'international space station']):
            mission = "ISS"
        elif any(keyword in title_lower for keyword in ['space shuttle', 'shuttle']):
            mission = "Space Shuttle"
        elif any(keyword in title_lower for keyword in ['artemis']):
            mission = "Artemis"
        elif any(keyword in title_lower for keyword in ['analog', 'simulated']):
            mission = "Analog Studies"
        elif any(keyword in title_lower for keyword in ['parabolic']):
            mission = "Parabolic Flight"
        
        # Determine environment
        environment = "Space Environment"
        if any(keyword in title_lower for keyword in ['microgravity', 'micro-gravity']):
            environment = "Microgravity"
        elif any(keyword in title_lower for keyword in ['radiation', 'irradiation']):
            environment = "Radiation"
        elif any(keyword in title_lower for keyword in ['hypergravity']):
            environment = "Hypergravity"
        elif any(keyword in title_lower for keyword in ['isolation', 'confined']):
            environment = "Isolation"
        
        # Create summary from abstract
        abstract = paper_data.get('abstract', '')
        summary = abstract[:200] + "..." if len(abstract) > 200 else abstract
        
        # Determine if has OSDR/DOI
        hasOSDR = 'osdr' in paper_data.get('url', '').lower() or 'osdr' in abstract.lower()
        hasDOI = bool(paper_data.get('doi', '').strip())
        
        cursor.execute("""
            INSERT INTO papers (title, url, organism, year, source, authors, mission, environment, summary, citations, hasOSDR, hasDOI, bookmarked, abstract, keyResults, methods, conclusions, doi, osdrLink, taskBookLink)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            paper_data["title"], 
            paper_data["url"], 
            organism, 
            paper_data["year"] or 2023, 
            paper_data["source"], 
            authors, 
            mission, 
            environment, 
            summary, 
            0,  # citations
            hasOSDR, 
            hasDOI, 
            False,  # bookmarked
            abstract, 
            "[]",  # keyResults
            "Not specified",  # methods
            "Not specified",  # conclusions
            paper_data.get("doi", ""), 
            "",  # osdrLink
            ""   # taskBookLink
        ))
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        print(f"Error adding paper: {e}")
        return None
    finally:
        conn.close()

def main():
    print("🔄 Importing papers from scraped_results.csv...")
    
    # Load papers from scraped results
    scraped_papers = load_scraped_papers('data/scraped_results.csv')
    print(f"📄 Loaded {len(scraped_papers)} papers from scraped results")
    
    # Get existing URLs
    existing_urls = get_existing_paper_urls()
    print(f"🗄️ Database has {len(existing_urls)} existing papers")
    
    # Find new papers
    new_papers = []
    for paper in scraped_papers:
        if paper['url'] not in existing_urls:
            new_papers.append(paper)
    
    print(f"🆕 Found {len(new_papers)} new papers to add")
    
    if not new_papers:
        print("✅ No new papers to add!")
        return
    
    # Add new papers to database
    added_count = 0
    error_count = 0
    
    for i, paper in enumerate(new_papers):
        print(f"Adding paper {i+1}/{len(new_papers)}: {paper['title'][:50]}...")
        
        paper_id = add_paper_to_database(paper)
        if paper_id:
            added_count += 1
            print(f"  ✅ Added with ID {paper_id}")
        else:
            error_count += 1
            print(f"  ❌ Failed to add")
    
    print(f"\n📊 Import complete!")
    print(f"✅ Successfully added: {added_count}")
    print(f"❌ Errors: {error_count}")
    
    # Update Elasticsearch
    print(f"\n🔄 Updating Elasticsearch...")
    try:
        from migrate_to_elasticsearch import migrate_papers_to_elasticsearch
        migrate_papers_to_elasticsearch()
        print("✅ Elasticsearch updated!")
    except Exception as e:
        print(f"❌ Error updating Elasticsearch: {e}")
    
    print(f"\n🎉 Import complete!")

if __name__ == "__main__":
    main()
