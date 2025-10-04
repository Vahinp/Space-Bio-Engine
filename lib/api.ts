// API service for connecting to the Flask backend
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:5003';

export interface Paper {
  id: string;
  title: string;
  url: string;
  organism?: string;
  year: number;
  source?: string;
  authors: string;
  mission: string;
  environment: string;
  summary: string;
  citations: number;
  hasOSDR: boolean;
  hasDOI: boolean;
  bookmarked: boolean;
  abstract: string;
  keyResults: string[];
  methods: string;
  conclusions: string;
  doi: string;
  osdrLink: string;
  taskBookLink?: string;
  score?: number;
  highlights?: {
    abstract?: string[];
    title?: string[];
  };
}

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  status: number;
}

class ApiService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = API_BASE_URL;
  }

  private async request<T>(endpoint: string, options?: RequestInit): Promise<ApiResponse<T>> {
    try {
      const url = `${this.baseUrl}${endpoint}`;
      console.log('🌐 Making API request to:', url);
      
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
        ...options,
      });

      console.log('📡 Response status:', response.status);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('📊 Response data length:', Array.isArray(data) ? data.length : 'Not an array');
      return { data, status: response.status };
    } catch (error) {
      console.error('💥 API request failed:', error);
      return {
        error: error instanceof Error ? error.message : 'Unknown error',
        status: 500,
      };
    }
  }

  // Health check
  async healthCheck(): Promise<ApiResponse<{ status: string; count: number }>> {
    return this.request('/api/health');
  }

  // Get all papers with pagination
  async getPapers(limit: number = 50, offset: number = 0): Promise<ApiResponse<Paper[]>> {
    return this.request(`/api/papers?limit=${limit}&offset=${offset}`);
  }

  // Get paper titles only
  async getPaperTitles(): Promise<ApiResponse<{ id: number; title: string }[]>> {
    return this.request('/api/papers/titles');
  }

  // Search papers with filters
  async searchPapers(query: string, filters?: {
    year_gte?: number;
    year_lte?: number;
    organism?: string;
    mission?: string;
    environment?: string;
    hasOSDR?: boolean;
    hasDOI?: boolean;
  }): Promise<ApiResponse<Paper[]>> {
    const params = new URLSearchParams();
    if (query) params.append('q', query);
    if (filters) {
      if (filters.year_gte) params.append('year_gte', filters.year_gte.toString());
      if (filters.year_lte) params.append('year_lte', filters.year_lte.toString());
      if (filters.organism) params.append('organism', filters.organism);
      if (filters.mission) params.append('mission', filters.mission);
      if (filters.environment) params.append('environment', filters.environment);
      if (filters.hasOSDR !== undefined) params.append('hasOSDR', filters.hasOSDR.toString());
      if (filters.hasDOI !== undefined) params.append('hasDOI', filters.hasDOI.toString());
    }
    return this.request(`/api/papers/search?${params.toString()}`);
  }

  // Enrich all papers with PMC data
  async enrichAllPapers(): Promise<ApiResponse<{
    success: boolean;
    total_papers: number;
    enriched_count: number;
    error_count: number;
    skipped_count: number;
    results: Array<{
      id: string;
      title: string;
      status: 'success' | 'error' | 'skipped';
      authors?: string;
      year?: number;
      abstract_length?: number;
      error?: string;
      reason?: string;
    }>;
  }>> {
    return this.request('/api/papers/enrich-all', {
      method: 'POST',
    });
  }

  // Add a new paper by URL
  async addPaper(url: string): Promise<ApiResponse<{
    success: boolean;
    message: string;
    paper: Paper;
  }>> {
    return this.request('/api/papers/add', {
      method: 'POST',
      body: JSON.stringify({ url }),
    });
  }
}

export const apiService = new ApiService();
