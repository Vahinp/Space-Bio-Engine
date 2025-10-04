#!/usr/bin/env python3
"""
API endpoint to parse existing PMC articles and enrich them with detailed information.
This will be called from the frontend to parse all loaded papers with abstracts, authors, DOIs, etc.
"""

import csv
import os
import sys
import time
from pmc_scrape import parse_pmc_article

def is_pmc_url(url):
    """Check if a URL is a PMC article URL."""
    return url and ('pmc.ncbi.nlm.nih.gov' in url or 'ncbi.nlm.nih.gov/pmc' in url)

def update_csv_with_pmc_data(csv_path="data/papers.csv", delay=1.0, max_articles=None):
    """
    Parse existing PMC articles in CSV and update them with detailed information.
    
    Args:
        csv_path: Path to the CSV file
        delay: Delay between requests (seconds)
        max_articles: Maximum number of articles to process (None for all)
    """
    
    if not os.path.exists(csv_path):
        print(f"❌ CSV file not found: {csv_path}")
        return
    
    # Read existing CSV
    print(f"📖 Reading existing CSV: {csv_path}")
    papers = []
    pmc_urls = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        print(f"📋 CSV columns: {fieldnames}")
        
        # Normalize field names (handle BOM character)
        normalized_fieldnames = []
        for field in fieldnames:
            normalized_field = field.replace('\ufeff', '')  # Remove BOM
            normalized_fieldnames.append(normalized_field)
        
        for i, row in enumerate(reader):
            # Normalize row keys to match normalized fieldnames
            normalized_row = {}
            for key, value in row.items():
                normalized_key = key.replace('\ufeff', '')
                normalized_row[normalized_key] = value
            papers.append(normalized_row)
            
            url = normalized_row.get('Link') or normalized_row.get('link') or normalized_row.get('url', '')
            
            if is_pmc_url(url):
                pmc_urls.append((i, url))
    
    print(f"📊 Found {len(papers)} total papers")
    print(f"🔬 Found {len(pmc_urls)} PMC articles to parse")
    
    if max_articles:
        pmc_urls = pmc_urls[:max_articles]
        print(f"🎯 Processing first {len(pmc_urls)} PMC articles")
    
    # Parse PMC articles
    parsed_count = 0
    error_count = 0
    
    for i, (row_index, url) in enumerate(pmc_urls):
        print(f"\n📄 Processing {i+1}/{len(pmc_urls)}: {url}")
        
        try:
            # Parse the PMC article
            result = parse_pmc_article(url)
            
            if result.get('error'):
                print(f"❌ Error parsing: {result.get('error')}")
                error_count += 1
                continue
            
            # Update the paper with parsed data
            paper = papers[row_index]
            
            # Update fields with parsed data
            if result.get('title'):
                paper['Title'] = result['title']
            
            if result.get('authors'):
                paper['authors'] = result['authors']
            
            if result.get('year'):
                paper['year'] = str(result['year'])
            
            if result.get('doi'):
                paper['doi'] = result['doi']
            
            if result.get('abstract'):
                paper['abstract'] = result['abstract']
            
            if result.get('pdf_url'):
                paper['pdf_url'] = result['pdf_url']
            
            if result.get('pmcid'):
                paper['pmcid'] = result['pmcid']
            
            # Set source to PMC if not already set
            if not paper.get('source'):
                paper['source'] = 'PMC'
            
            print(f"✅ Successfully parsed: {result.get('title', 'Unknown')[:60]}...")
            print(f"   Authors: {result.get('authors', 'Unknown')}")
            print(f"   Year: {result.get('year', 'Unknown')}")
            print(f"   Abstract: {len(result.get('abstract', ''))} chars")
            
            parsed_count += 1
            
        except Exception as e:
            print(f"❌ Exception parsing {url}: {str(e)}")
            error_count += 1
        
        # Delay between requests
        if i < len(pmc_urls) - 1:
            time.sleep(delay)
    
    # Write updated CSV
    print(f"\n💾 Writing updated CSV with {parsed_count} enriched articles...")
    
    # Ensure all new fields are in normalized_fieldnames
    new_fields = ['authors', 'year', 'doi', 'abstract', 'pdf_url', 'pmcid', 'source']
    for field in new_fields:
        if field not in normalized_fieldnames:
            normalized_fieldnames.append(field)
    
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=normalized_fieldnames)
        writer.writeheader()
        
        for paper in papers:
            # Ensure all fields exist
            for field in normalized_fieldnames:
                if field not in paper:
                    paper[field] = ''
            writer.writerow(paper)
    
    print(f"\n🎉 Processing complete!")
    print(f"✅ Successfully parsed: {parsed_count} articles")
    print(f"❌ Errors: {error_count} articles")
    print(f"📊 Total papers in CSV: {len(papers)}")
    print(f"💾 Updated CSV saved to: {csv_path}")

def main():
    """Main function with command line argument handling."""
    
    print("PMC Article Parser for Existing CSV")
    print("=" * 50)
    
    # Parse command line arguments
    csv_path = "data/papers.csv"
    delay = 1.0
    max_articles = None
    
    if len(sys.argv) > 1:
        csv_path = sys.argv[1]
    if len(sys.argv) > 2:
        delay = float(sys.argv[2])
    if len(sys.argv) > 3:
        max_articles = int(sys.argv[3])
    
    print(f"📁 CSV file: {csv_path}")
    print(f"⏱️  Delay: {delay} seconds")
    print(f"🎯 Max articles: {max_articles or 'All'}")
    
    # Confirm before proceeding (skip if max_articles is set for automated testing)
    if max_articles is None:
        response = input(f"\nParse PMC articles and update CSV? (y/N): ")
        if response.lower() != 'y':
            print("Cancelled.")
            return
    else:
        print(f"\n🤖 Auto-processing {max_articles} articles...")
    
    # Process the CSV
    update_csv_with_pmc_data(csv_path, delay, max_articles)

if __name__ == "__main__":
    main()
