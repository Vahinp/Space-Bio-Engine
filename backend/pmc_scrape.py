import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime
import time

DOI_RE = re.compile(r'^https?://doi\.org/.+', re.I)

def parse_pmc_article(url: str):
    """Return dict with title, doi, abstract, pdf_url, pmcid, html_url, and publication date."""
    html_url = url.split('#')[0]  # normalize fragmentless
    
    try:
        # Add proper headers to avoid 403 errors
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        resp = requests.get(html_url, headers=headers, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # 1) Title (robust: page H1 is the article title on PMC)
        title_el = soup.select_one("h1")
        title = title_el.get_text(strip=True) if title_el else None

        # 2) DOI (anchor that starts with https://doi.org/)
        doi_el = soup.select_one('a[href^="https://doi.org/"]')
        doi = doi_el.get("href") if doi_el else None

        # 3) Abstract (PMC marks the Abstract section; catch typical patterns)
        abstract = None
        # try section with id starting 'abstract'
        abs_section = soup.select_one('section[id^="abstract"], div[id^="abstract"]')
        if abs_section:
            # remove nested headings, keep paragraph text
            for h in abs_section.find_all(['h2','h3','header']):
                h.decompose()
            abstract = " ".join(p.get_text(" ", strip=True) for p in abs_section.find_all(['p','div']) if p.get_text(strip=True))
        else:
            # fallback: the "Abstract" heading followed by text
            heading = soup.find(lambda tag: tag.name in ['h2','h3'] and 'abstract' in tag.get_text(strip=True).lower())
            if heading:
                sib_texts = []
                for sib in heading.find_all_next():
                    # stop at next top-level section heading
                    if sib.name in ['h2','h3'] and sib is not heading:
                        break
                    if sib.name in ['p','div'] and sib.get_text(strip=True):
                        sib_texts.append(sib.get_text(" ", strip=True))
                abstract = " ".join(sib_texts) or None

        # 4) PDF URL
        pdf_el = soup.select_one('a[href$=".pdf"], a[href*="/pdf/"]')
        pdf_url = urljoin(html_url, pdf_el.get("href")) if pdf_el else None

        # If missing, synthesize from canonical PMCID path: /articles/PMCID/pdf
        if not pdf_url:
            path = urlparse(html_url).path.rstrip('/')
            if path.startswith("/articles/PMCID") or "/articles/PMC" in path:
                parts = [p for p in path.split('/') if p]
                try:
                    pmcid = next(p for p in parts if p.startswith("PMC"))
                    pdf_url = urljoin(html_url, f"/articles/{pmcid}/pdf")
                except StopIteration:
                    pass

        # 5) PMCID
        pmcid = None
        pmcid_text = soup.find(string=re.compile(r'^PMCID:\s*PMC\d+', re.I))
        if pmcid_text:
            m = re.search(r'(PMC\d+)', pmcid_text)
            if m:
                pmcid = m.group(1)

        # 6) Publication Date - look for various date patterns
        pub_date = None
        year = None
        
        # Try to find publication date in various formats
        date_patterns = [
            r'Published\s+(\d{4})',  # "Published 2013"
            r'(\d{4})\s+[A-Za-z]+\s+\d{1,2}',  # "2013 May 15"
            r'(\d{1,2})\s+[A-Za-z]+\s+(\d{4})',  # "15 May 2013"
            r'[A-Za-z]+\s+(\d{1,2}),\s+(\d{4})',  # "May 15, 2013"
        ]
        
        # Look in the page content for date patterns
        page_text = soup.get_text()
        for pattern in date_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                if len(match.groups()) == 1:
                    year = int(match.group(1))
                else:
                    year = int(match.group(2)) if match.group(2) else int(match.group(1))
                break
        
        # Also try to find date in meta tags
        if not year:
            date_meta = soup.find('meta', {'name': re.compile(r'date|pub', re.I)})
            if date_meta and date_meta.get('content'):
                date_content = date_meta.get('content')
                year_match = re.search(r'(\d{4})', date_content)
                if year_match:
                    year = int(year_match.group(1))

        # 7) Authors - try to extract from various locations
        authors = "Unknown Author"
        
        # Look for author information in meta tags or structured data
        author_meta = soup.find('meta', {'name': re.compile(r'author|creator', re.I)})
        if author_meta and author_meta.get('content'):
            authors = author_meta.get('content')
        else:
            # Try to find author names in the page content
            author_section = soup.find(['div', 'section'], class_=re.compile(r'author|contrib', re.I))
            if author_section:
                author_links = author_section.find_all('a')
                if author_links:
                    authors = ', '.join([link.get_text(strip=True) for link in author_links[:3]])  # First 3 authors
                else:
                    author_text = author_section.get_text(strip=True)
                    if author_text and len(author_text) < 200:  # Reasonable author text length
                        authors = author_text

        return {
            "title": title,
            "doi": doi if (doi and DOI_RE.match(doi)) else None,
            "abstract": abstract,
            "pdf_url": pdf_url,
            "pmcid": pmcid,
            "html_url": html_url,
            "year": year or 2023,  # Default to 2023 if no year found
            "authors": authors,
            "source": "PMC"
        }
        
    except Exception as e:
        print(f"Error parsing PMC article {url}: {str(e)}")
        return {
            "title": "Error parsing article",
            "doi": None,
            "abstract": f"Error: {str(e)}",
            "pdf_url": None,
            "pmcid": None,
            "html_url": html_url,
            "year": 2023,
            "authors": "Unknown",
            "source": "PMC",
            "error": str(e)
        }

def batch_parse_pmc_articles(urls: list, delay: float = 1.0):
    """Parse multiple PMC articles with delay between requests."""
    results = []
    for i, url in enumerate(urls):
        print(f"Parsing article {i+1}/{len(urls)}: {url}")
        result = parse_pmc_article(url)
        results.append(result)
        
        # Be respectful with delays
        if i < len(urls) - 1:  # Don't delay after the last request
            time.sleep(delay)
    
    return results

if __name__ == "__main__":
    # Test with the example URL
    test_url = "https://pmc.ncbi.nlm.nih.gov/articles/PMC3630201/#abstract1"
    print(f"Testing PMC scraper with: {test_url}")
    data = parse_pmc_article(test_url)
    
    from pprint import pprint
    print("\n=== Parsed Data ===")
    pprint(data)
    
    # Test batch parsing
    test_urls = [
        "https://pmc.ncbi.nlm.nih.gov/articles/PMC3630201/#abstract1",
        # Add more URLs here for testing
    ]
    
    print(f"\n=== Batch Parsing {len(test_urls)} URLs ===")
    batch_results = batch_parse_pmc_articles(test_urls)
    for i, result in enumerate(batch_results):
        print(f"\nArticle {i+1}:")
        print(f"  Title: {result.get('title', 'N/A')}")
        print(f"  Year: {result.get('year', 'N/A')}")
        print(f"  Authors: {result.get('authors', 'N/A')}")
        print(f"  DOI: {result.get('doi', 'N/A')}")
        print(f"  Abstract length: {len(result.get('abstract', '')) if result.get('abstract') else 0} chars")
