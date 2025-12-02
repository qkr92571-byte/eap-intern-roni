/**
 * 경쟁사 동향 데이터를 관리하는 커스텀 훅
 */

import { useState, useEffect } from 'react';
import { getCompetitorAwards } from '../services/api';

interface UseCompetitorAwardsOptions {
  limit?: number;
  autoLoad?: boolean;
}

export const useCompetitorAwards = (options: UseCompetitorAwardsOptions = {}) => {
  const { limit = 100, autoLoad = true } = options;
  
  const [awards, setAwards] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadAwards = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await getCompetitorAwards({ limit });
      
      if (response.success && response.data) {
        setAwards(response.data);
      } else {
        setError(response.error || '경쟁사 동향을 불러오는데 실패했습니다.');
      }
    } catch (err: any) {
      const errorMessage = err.message || '경쟁사 동향을 불러오는데 실패했습니다.';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (autoLoad) {
      loadAwards();
    }
  }, [limit, autoLoad]);

  return {
    awards,
    loading,
    error,
    reload: loadAwards,
  };
};

