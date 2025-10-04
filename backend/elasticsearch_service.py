#!/usr/bin/env python3
"""
Elasticsearch service for Space Bio Engine
Handles indexing and searching of research papers
"""

import os
import json
import requests
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ElasticsearchService:
    def __init__(self):
        self.es_endpoint = os.getenv("ES_ENDPOINT", "http://localhost:9200")
        self.es_api_key = os.getenv("ES_API_KEY")
        self.index_name = "space_bio_papers"
        
        self.headers = {
            "Content-Type": "application/json"
        }
        
        if self.es_api_key:
            self.headers["Authorization"] = f"ApiKey {self.es_api_key}"
        
        # Create index if it doesn't exist
        self._create_index()
    
    def _create_index(self):
        """Create the Elasticsearch index with proper mapping"""
        mapping = {
            "mappings": {
                "properties": {
                    "paper_id": {"type": "keyword"},
                    "title": {
                        "type": "text",
                        "analyzer": "english",
                        "fields": {
                            "keyword": {"type": "keyword"},
                            "suggest": {"type": "completion"}
                        }
                    },
                    "abstract": {
                        "type": "text",
                        "analyzer": "english"
                    },
                    "authors": {
                        "type": "text",
                        "analyzer": "english",
                        "fields": {
                            "keyword": {"type": "keyword"}
                        }
                    },
                    "venue": {"type": "keyword"},
                    "source": {"type": "keyword"},
                    "date": {"type": "date"},
                    "year": {"type": "integer"},
                    "url": {"type": "keyword"},
                    "doi": {"type": "keyword"},
                    "pmcid": {"type": "keyword"},
                    "keywords": {
                        "type": "text",
                        "analyzer": "english"
                    },
                    "organism": {"type": "keyword"},
                    "mission": {"type": "keyword"},
                    "environment": {"type": "keyword"},
                    "citations": {"type": "integer"},
                    "hasOSDR": {"type": "boolean"},
                    "hasDOI": {"type": "boolean"},
                    "bookmarked": {"type": "boolean"},
                    "summary": {"type": "text", "analyzer": "english"},
                    "methods": {"type": "text", "analyzer": "english"},
                    "conclusions": {"type": "text", "analyzer": "english"},
                    "keyResults": {"type": "text", "analyzer": "english"},
                    "pdf_url": {"type": "keyword"},
                    "taskBookLink": {"type": "keyword"},
                    "created_at": {"type": "date"},
                    "updated_at": {"type": "date"}
                }
            },
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "analysis": {
                    "analyzer": {
                        "english": {
                            "type": "standard",
                            "stopwords": "_english_"
                        }
                    }
                }
            }
        }
        
        try:
            # Check if index exists
            response = requests.get(f"{self.es_endpoint}/{self.index_name}", headers=self.headers)
            if response.status_code == 404:
                # Create index
                response = requests.put(
                    f"{self.es_endpoint}/{self.index_name}",
                    headers=self.headers,
                    data=json.dumps(mapping)
                )
                if response.status_code == 200:
                    logger.info(f"✅ Created index: {self.index_name}")
                else:
                    logger.error(f"❌ Failed to create index: {response.text}")
            else:
                logger.info(f"✅ Index {self.index_name} already exists")
        except Exception as e:
            logger.error(f"❌ Error creating index: {str(e)}")
    
    def index_paper(self, paper: Dict[str, Any]) -> bool:
        """Index a single paper"""
        try:
            # Prepare document for indexing
            doc = {
                "paper_id": paper.get("id"),
                "title": paper.get("title", ""),
                "abstract": paper.get("abstract", ""),
                "authors": paper.get("authors", ""),
                "venue": paper.get("source", ""),
                "source": paper.get("source", ""),
                "date": paper.get("date", f"{paper.get('year', 2023)}-01-01"),
                "year": paper.get("year", 2023),
                "url": paper.get("url", ""),
                "doi": paper.get("doi", ""),
                "pmcid": paper.get("pmcid", ""),
                "keywords": paper.get("keywords", ""),
                "organism": paper.get("organism", ""),
                "mission": paper.get("mission", ""),
                "environment": paper.get("environment", ""),
                "citations": paper.get("citations", 0),
                "hasOSDR": paper.get("hasOSDR", False),
                "hasDOI": paper.get("hasDOI", False),
                "bookmarked": paper.get("bookmarked", False),
                "summary": paper.get("summary", ""),
                "methods": paper.get("methods", ""),
                "conclusions": paper.get("conclusions", ""),
                "keyResults": " ".join(paper.get("keyResults", [])),
                "pdf_url": paper.get("pdf_url", ""),
                "taskBookLink": paper.get("taskBookLink", ""),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            # Index the document
            response = requests.put(
                f"{self.es_endpoint}/{self.index_name}/_doc/{doc['paper_id']}",
                headers=self.headers,
                data=json.dumps(doc)
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"✅ Indexed paper: {doc['title'][:50]}...")
                return True
            else:
                logger.error(f"❌ Failed to index paper: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error indexing paper: {str(e)}")
            return False
    
    def bulk_index_papers(self, papers: List[Dict[str, Any]]) -> Dict[str, int]:
        """Bulk index multiple papers"""
        success_count = 0
        error_count = 0
        
        for paper in papers:
            if self.index_paper(paper):
                success_count += 1
            else:
                error_count += 1
        
        return {"success": success_count, "errors": error_count}
    
    def search_papers(
        self,
        query: str = "",
        filters: Optional[Dict[str, Any]] = None,
        size: int = 10,
        from_: int = 0
    ) -> Dict[str, Any]:
        """Search papers with advanced querying"""
        
        if filters is None:
            filters = {}
        
        # Build filter clauses
        filter_clauses = []
        
        if filters.get("year_gte"):
            filter_clauses.append({"range": {"year": {"gte": filters["year_gte"]}}})
        
        if filters.get("year_lte"):
            filter_clauses.append({"range": {"year": {"lte": filters["year_lte"]}}})
        
        if filters.get("organism"):
            filter_clauses.append({"term": {"organism": filters["organism"]}})
        
        if filters.get("mission"):
            filter_clauses.append({"term": {"mission": filters["mission"]}})
        
        if filters.get("environment"):
            filter_clauses.append({"term": {"environment": filters["environment"]}})
        
        if filters.get("venue"):
            filter_clauses.append({"term": {"venue": filters["venue"]}})
        
        if filters.get("hasOSDR"):
            filter_clauses.append({"term": {"hasOSDR": True}})
        
        if filters.get("hasDOI"):
            filter_clauses.append({"term": {"hasDOI": True}})
        
        # Build search query
        search_body = {
            "size": size,
            "from": from_,
            "query": {
                "function_score": {
                    "query": {
                        "bool": {
                            "must": [],
                            "filter": filter_clauses
                        }
                    },
                    "functions": [
                        {
                            "gauss": {
                                "date": {
                                    "origin": "now",
                                    "scale": "365d",
                                    "decay": 0.5
                                }
                            },
                            "weight": 1.0
                        }
                    ],
                    "score_mode": "sum",
                    "boost_mode": "sum"
                }
            },
            "highlight": {
                "fields": {
                    "abstract": {"fragment_size": 150, "number_of_fragments": 3},
                    "title": {"fragment_size": 100, "number_of_fragments": 1}
                }
            },
            "sort": [
                {"_score": {"order": "desc"}},
                {"year": {"order": "desc"}}
            ]
        }
        
        # Add text search if query provided
        if query.strip():
            search_body["query"]["function_score"]["query"]["bool"]["must"].append({
                "multi_match": {
                    "query": query,
                    "type": "most_fields",
                    "fields": [
                        "title^3",
                        "abstract^2",
                        "authors^1.5",
                        "keywords^2",
                        "summary^1.5",
                        "methods^1",
                        "conclusions^1"
                    ],
                    "fuzziness": "AUTO"
                }
            })
        else:
            # If no query, match all documents
            search_body["query"]["function_score"]["query"]["bool"]["must"].append({
                "match_all": {}
            })
        
        try:
            response = requests.post(
                f"{self.es_endpoint}/{self.index_name}/_search",
                headers=self.headers,
                data=json.dumps(search_body)
            )
            
            if response.status_code == 200:
                data = response.json()
                hits = data.get("hits", {})
                
                results = []
                for hit in hits.get("hits", []):
                    source = hit["_source"]
                    result = {
                        "id": source["paper_id"],
                        "title": source["title"],
                        "abstract": source["abstract"],
                        "authors": source["authors"],
                        "year": source["year"],
                        "venue": source["venue"],
                        "url": source["url"],
                        "doi": source["doi"],
                        "score": hit["_score"],
                        "highlights": hit.get("highlight", {})
                    }
                    results.append(result)
                
                return {
                    "total": hits.get("total", {}).get("value", 0),
                    "results": results,
                    "took": data.get("took", 0)
                }
            else:
                logger.error(f"❌ Search failed: {response.text}")
                return {"total": 0, "results": [], "took": 0}
                
        except Exception as e:
            logger.error(f"❌ Search error: {str(e)}")
            return {"total": 0, "results": [], "took": 0}
    
    def get_aggregations(self) -> Dict[str, Any]:
        """Get aggregations for faceted search"""
        agg_body = {
            "size": 0,
            "aggs": {
                "by_year": {
                    "date_histogram": {
                        "field": "date",
                        "calendar_interval": "year",
                        "min_doc_count": 1
                    }
                },
                "by_organism": {
                    "terms": {
                        "field": "organism",
                        "size": 20
                    }
                },
                "by_mission": {
                    "terms": {
                        "field": "mission",
                        "size": 20
                    }
                },
                "by_environment": {
                    "terms": {
                        "field": "environment",
                        "size": 20
                    }
                },
                "by_venue": {
                    "terms": {
                        "field": "venue",
                        "size": 20
                    }
                }
            }
        }
        
        try:
            response = requests.post(
                f"{self.es_endpoint}/{self.index_name}/_search",
                headers=self.headers,
                data=json.dumps(agg_body)
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("aggregations", {})
            else:
                logger.error(f"❌ Aggregations failed: {response.text}")
                return {}
                
        except Exception as e:
            logger.error(f"❌ Aggregations error: {str(e)}")
            return {}
    
    def delete_index(self) -> bool:
        """Delete the entire index"""
        try:
            response = requests.delete(f"{self.es_endpoint}/{self.index_name}", headers=self.headers)
            if response.status_code == 200:
                logger.info(f"✅ Deleted index: {self.index_name}")
                return True
            else:
                logger.error(f"❌ Failed to delete index: {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ Error deleting index: {str(e)}")
            return False

# Global instance
es_service = ElasticsearchService()
