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
  searchPapers: (query: string) => void;
  clearSearch: () => void;
}

export function usePapers(): UsePapersReturn {
  const [papers, setPapers] = useState<Paper[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

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

  const searchPapers = useCallback(async (query: string) => {
    if (!query.trim()) {
      loadPapers();
      return;
    }

    setLoading(true);
    setError(null);
    
    try {
      const response = await apiService.searchPapers(query);
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

  // Load papers on mount
  useEffect(() => {
    loadPapers();
  }, [loadPapers]);

  // Search when query changes
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (searchQuery) {
        searchPapers(searchQuery);
      } else {
        loadPapers();
      }
    }, 300); // Debounce search

    return () => clearTimeout(timeoutId);
  }, [searchQuery, searchPapers, loadPapers]);

  return {
    papers,
    loading,
    error,
    searchQuery,
    setSearchQuery,
    refreshPapers,
    searchPapers,
    clearSearch,
  };
}
