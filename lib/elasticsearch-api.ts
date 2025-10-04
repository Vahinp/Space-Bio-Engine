// Elasticsearch API service for advanced search capabilities
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:5001';

export interface ElasticsearchPaper {
  id: string;
  title: string;
  abstract: string;
  authors: string;
  year: number;
  venue: string;
  url: string;
  doi: string;
  score: number;
  highlights?: {
    abstract?: string[];
    title?: string[];
  };
}

export interface SearchFilters {
  year_gte?: number;
  year_lte?: number;
  organism?: string;
  mission?: string;
  environment?: string;
  venue?: string;
  hasOSDR?: boolean;
  hasDOI?: boolean;
}

export interface SearchResponse {
  total: number;
  results: ElasticsearchPaper[];
  took: number;
}

export interface Aggregations {
  by_year?: {
    buckets: Array<{
      key_as_string: string;
      key: number;
      doc_count: number;
    }>;
  };
  by_organism?: {
    buckets: Array<{
      key: string;
      doc_count: number;
    }>;
  };
  by_mission?: {
    buckets: Array<{
      key: string;
      doc_count: number;
    }>;
  };
  by_environment?: {
    buckets: Array<{
      key: string;
      doc_count: number;
    }>;
  };
  by_venue?: {
    buckets: Array<{
      key: string;
      doc_count: number;
    }>;
  };
}

class ElasticsearchApiService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = API_BASE_URL;
  }

  private async request<T>(endpoint: string, options?: RequestInit): Promise<ApiResponse<T>> {
    try {
      const url = `${this.baseUrl}${endpoint}`;
      console.log('🔍 Elasticsearch API request:', url);
      
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
        ...options,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return { data, status: response.status };
    } catch (error) {
      console.error('💥 Elasticsearch API request failed:', error);
      return {
        error: error instanceof Error ? error.message : 'Unknown error',
        status: 500,
      };
    }
  }

  // Health check
  async healthCheck(): Promise<ApiResponse<{
    status: string;
    elasticsearch: string;
    total_papers: number;
  }>> {
    return this.request('/api/health');
  }

  // Search papers with advanced filtering
  async searchPapers(
    query: string = '',
    filters: SearchFilters = {},
    size: number = 10,
    from: number = 0
  ): Promise<ApiResponse<SearchResponse>> {
    const params = new URLSearchParams({
      q: query,
      size: size.toString(),
      from: from.toString(),
    });

    // Add filters to params
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        params.append(key, value.toString());
      }
    });

    return this.request(`/api/elasticsearch/search?${params.toString()}`);
  }

  // Get aggregations for faceted search
  async getAggregations(): Promise<ApiResponse<Aggregations>> {
    return this.request('/api/elasticsearch/aggregations');
  }

  // Get search suggestions
  async getSuggestions(query: string): Promise<ApiResponse<{
    suggestions: Array<{
      text: string;
      id: string;
      year: number;
    }>;
  }>> {
    return this.request('/api/elasticsearch/suggest', {
      method: 'POST',
      body: JSON.stringify({ query }),
    });
  }

  // Index all papers (admin function)
  async indexAllPapers(): Promise<ApiResponse<{
    success: boolean;
    message: string;
    indexed: number;
    errors: number;
    total: number;
  }>> {
    return this.request('/api/elasticsearch/index-all', {
      method: 'POST',
    });
  }
}

export const elasticsearchApiService = new ElasticsearchApiService();
