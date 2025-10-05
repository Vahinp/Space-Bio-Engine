from elasticsearch import Elasticsearch
import sqlite3

# Connect to Elasticsearch
es = Elasticsearch("http://localhost:9200")

# Connect to the SQLite DB
conn = sqlite3.connect("data/papers.db")
cursor = conn.cursor()

# --- FIX: check if index exists safely for ES 8.x ---
try:
    exists = es.indices.exists(index="space_bio_papers")
except Exception as e:
    print("⚠️ Could not check index existence:", e)
    exists = False

# --- FIX: only create if not exists ---
if not exists:
    es.indices.create(index="space_bio_papers", ignore=400)
    print("📚 Created new index: space_bio_papers")

# Pull all papers
cursor.execute("SELECT id, title, authors, year, abstract, mission, organism, environment, url FROM papers")
rows = cursor.fetchall()

count = 0
for r in rows:
    doc = {
        "id": r[0],
        "title": r[1],
        "authors": r[2],
        "year": r[3],
        "abstract": r[4],
        "mission": r[5],
        "organism": r[6],
        "environment": r[7],
        "url": r[8],
    }
    # --- FIX: ES 8.x prefers "document=" keyword ---
    es.index(index="space_bio_papers", id=r[0], document=doc)
    count += 1

print(f"✅ Indexed {count} papers into Elasticsearch!")
