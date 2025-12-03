/**
 * 공고 데이터를 관리하는 커스텀 훅
 */

import { useState, useEffect } from 'react';
import { getAnnouncements } from '../services/api';
import { Announcement } from '../types';

interface UseAnnouncementsOptions {
  limit?: number;
  status?: string;
  autoLoad?: boolean;
}

export const useAnnouncements = (options: UseAnnouncementsOptions = {}) => {
  const { limit = 100, status, autoLoad = true } = options;
  
  const [announcements, setAnnouncements] = useState<Announcement[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadAnnouncements = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await getAnnouncements({ limit, status });
      
      if (response.success && response.data) {
        setAnnouncements(response.data);
      } else {
        setError(response.error || '공고 목록을 불러오는데 실패했습니다.');
      }
    } catch (err: any) {
      const errorMessage = err.message || '공고 목록을 불러오는데 실패했습니다.';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (autoLoad) {
      loadAnnouncements();
    }
  }, [limit, status, autoLoad]);

  return {
    announcements,
    loading,
    error,
    reload: loadAnnouncements,
  };
};


