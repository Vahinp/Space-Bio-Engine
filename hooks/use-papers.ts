'use client';

import { useState, useEffect, useCallback } from 'react';
import { apiService, Paper } from '@/lib/api';

interface UsePapersReturn {
  papers: Paper[];
  loading: boolean;
  error: string | null;
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  refreshPapers: () => void;
  searchPapers: (query: string, filters?: {
    year_gte?: number;
    year_lte?: number;
    organism?: string;
    mission?: string;
    environment?: string;
    hasOSDR?: boolean;
    hasDOI?: boolean;
  }) => void;
  clearSearch: () => void;
  enriching: boolean;
  enrichAllPapers: () => Promise<void>;
  enrichmentStatus: {
    total: number;
    enriched: number;
    errors: number;
    skipped: number;
  } | null;
}

export function usePapers(): UsePapersReturn {
  const [papers, setPapers] = useState<Paper[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [enriching, setEnriching] = useState(false);
  const [enrichmentStatus, setEnrichmentStatus] = useState<{
    total: number;
    enriched: number;
    errors: number;
    skipped: number;
  } | null>(null);

  const loadPapers = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    console.log('🔄 Loading papers from backend...');
    
    try {
      const response = await apiService.getPapers(1000); // Load up to 1000 papers
      console.log('📡 API Response:', response);
      
      if (response.error) {
        console.error('❌ API Error:', response.error);
        setError(response.error);
      } else if (response.data) {
        console.log('✅ Papers loaded successfully:', response.data.length, 'papers');
        console.log('📄 First few papers:', response.data.slice(0, 3));
        setPapers(response.data);
      }
    } catch (err) {
      console.error('💥 Load papers error:', err);
      setError(err instanceof Error ? err.message : 'Failed to load papers');
    } finally {
      setLoading(false);
    }
  }, []);

  const searchPapers = useCallback(async (query: string, filters?: {
    year_gte?: number;
    year_lte?: number;
    organism?: string;
    mission?: string;
    environment?: string;
    hasOSDR?: boolean;
    hasDOI?: boolean;
  }) => {
    if (!query.trim() && !filters) {
      loadPapers();
      return;
    }

    setLoading(true);
    setError(null);
    
    try {
      const response = await apiService.searchPapers(query, filters);
      if (response.error) {
        setError(response.error);
      } else if (response.data) {
        setPapers(response.data);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed');
    } finally {
      setLoading(false);
    }
  }, [loadPapers]);

  const clearSearch = useCallback(() => {
    setSearchQuery('');
    loadPapers();
  }, [loadPapers]);

  const refreshPapers = useCallback(() => {
    if (searchQuery) {
      searchPapers(searchQuery);
    } else {
      loadPapers();
    }
  }, [searchQuery, searchPapers, loadPapers]);

  const enrichAllPapers = useCallback(async () => {
    setEnriching(true);
    setError(null);
    
    console.log('🔬 Starting to enrich all papers with PMC data...');
    
    try {
      const response = await apiService.enrichAllPapers();
      console.log('📡 Enrichment API Response:', response);
      
      if (response.error) {
        console.error('❌ Enrichment API Error:', response.error);
        setError(response.error);
      } else if (response.data) {
        console.log('✅ Papers enriched successfully:', response.data);
        setEnrichmentStatus({
          total: response.data.total_papers,
          enriched: response.data.enriched_count,
          errors: response.data.error_count,
          skipped: response.data.skipped_count,
        });
        
        // Reload papers to get the enriched data
        await loadPapers();
      }
    } catch (err) {
      console.error('💥 Enrichment error:', err);
      setError(err instanceof Error ? err.message : 'Failed to enrich papers');
    } finally {
      setEnriching(false);
    }
  }, [loadPapers]);

  // Load papers on mount only
  useEffect(() => {
    loadPapers();
  }, []); // Empty dependency array to run only once

  // Disabled auto-search to prevent infinite loops
  // Search only when explicitly triggered by user
  // useEffect(() => {
  //   const timeoutId = setTimeout(() => {
  //     if (searchQuery.trim()) {
  //       searchPapers(searchQuery);
  //     } else {
  //       loadPapers();
  //     }
  //   }, 500); // 500ms debounce to prevent too many requests

  //   return () => clearTimeout(timeoutId);
  // }, [searchQuery, searchPapers, loadPapers]);

  return {
    papers,
    loading,
    error,
    searchQuery,
    setSearchQuery,
    refreshPapers,
    searchPapers,
    clearSearch,
    enriching,
    enrichAllPapers,
    enrichmentStatus,
  };
}
