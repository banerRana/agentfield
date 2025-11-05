import { useState, useEffect, useCallback, useRef } from 'react';
import type {
  EnhancedDashboardResponse,
  DashboardError
} from '../types/dashboard';
import { getEnhancedDashboardSummary } from '../services/dashboardService';

interface EnhancedDashboardOptions {
  refreshInterval?: number;
  cacheTtl?: number;
  onDataUpdate?: (data: EnhancedDashboardResponse) => void;
  onError?: (error: DashboardError) => void;
}

interface EnhancedDashboardState {
  data: EnhancedDashboardResponse | null;
  loading: boolean;
  error: DashboardError | null;
  lastFetch: Date | null;
  isStale: boolean;
}

export function useEnhancedDashboard(options: EnhancedDashboardOptions = {}) {
  const {
    refreshInterval = 45000,
    cacheTtl = 60000,
    onDataUpdate,
    onError
  } = options;

  const [state, setState] = useState<EnhancedDashboardState>({
    data: null,
    loading: false,
    error: null,
    lastFetch: null,
    isStale: false
  });

  const refreshTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const mountedRef = useRef(true);
  const cacheRef = useRef<{ data: EnhancedDashboardResponse | null; timestamp: number }>({
    data: null,
    timestamp: 0
  });

  const clearRefreshTimeout = useCallback(() => {
    if (refreshTimeoutRef.current) {
      clearTimeout(refreshTimeoutRef.current);
      refreshTimeoutRef.current = null;
    }
  }, []);

  const isCacheValid = useCallback(() => {
    if (!cacheRef.current.data) {
      return false;
    }
    return Date.now() - cacheRef.current.timestamp < cacheTtl;
  }, [cacheTtl]);

  const handleData = useCallback((data: EnhancedDashboardResponse) => {
    if (!mountedRef.current) {
      return;
    }

    cacheRef.current = {
      data,
      timestamp: Date.now()
    };

    setState(prev => ({
      ...prev,
      data,
      loading: false,
      error: null,
      lastFetch: new Date(),
      isStale: false
    }));

    onDataUpdate?.(data);
  }, [onDataUpdate]);

  const handleError = useCallback((error: Error) => {
    if (!mountedRef.current) {
      return;
    }

    const dashboardError: DashboardError = {
      message: error.message,
      code: error.name,
      details: error
    };

    setState(prev => ({
      ...prev,
      loading: false,
      error: dashboardError,
      isStale: true
    }));

    onError?.(dashboardError);
  }, [onError]);

  const fetchDashboard = useCallback(async (force = false) => {
    if (!mountedRef.current) {
      return;
    }

    if (!force && isCacheValid()) {
      const cached = cacheRef.current.data;
      if (cached) {
        handleData(cached);
        return;
      }
    }

    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const data = await getEnhancedDashboardSummary();
      handleData(data);
    } catch (error) {
      handleError(error as Error);
    }
  }, [handleData, handleError, isCacheValid]);

  const scheduleRefresh = useCallback(() => {
    if (refreshInterval > 0) {
      clearRefreshTimeout();
      refreshTimeoutRef.current = setTimeout(() => {
        fetchDashboard();
      }, refreshInterval);
    }
  }, [clearRefreshTimeout, fetchDashboard, refreshInterval]);

  const refresh = useCallback(() => {
    fetchDashboard(true);
  }, [fetchDashboard]);

  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: null, isStale: false }));
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    fetchDashboard();

    return () => {
      mountedRef.current = false;
      clearRefreshTimeout();
    };
  }, [fetchDashboard, clearRefreshTimeout]);

  useEffect(() => {
    if (state.data && !state.loading) {
      scheduleRefresh();
    }
  }, [scheduleRefresh, state.data, state.loading]);

  return {
    ...state,
    refresh,
    clearError,
    hasData: state.data !== null,
    hasError: state.error !== null,
    isRefreshing: state.loading && state.data !== null
  };
}

export function useEnhancedDashboardSimple() {
  return useEnhancedDashboard({
    refreshInterval: 45000
  });
}
