/**
 * 공고 통계를 관리하는 커스텀 훅
 */

import { useState, useEffect } from 'react';
import { getAnnouncements } from '../services/api';
import { Stats } from '../types';
import { ANNOUNCEMENT_STATUS } from '../utils/constants';

export const useStats = () => {
  const [stats, setStats] = useState<Stats>({
    total: 0,
    approved: 0,
    pending: 0,
    rejected: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadStats = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await getAnnouncements({ limit: 1000 });
      
      if (response.success && response.data) {
        const announcements = response.data;
        setStats({
          total: announcements.length,
          approved: announcements.filter((a) => a.status === ANNOUNCEMENT_STATUS.APPROVED).length,
          pending: announcements.filter((a) => a.status === ANNOUNCEMENT_STATUS.PENDING).length,
          rejected: announcements.filter((a) => a.status === ANNOUNCEMENT_STATUS.REJECTED).length,
        });
      } else {
        setError(response.error || '통계를 불러오는데 실패했습니다.');
      }
    } catch (err: any) {
      const errorMessage = err.message || '통계를 불러오는데 실패했습니다.';
      setError(errorMessage);
      
      if (err.message?.includes('Network Error') || err.code === 'ECONNREFUSED') {
        console.error('백엔드 서버가 실행되지 않았습니다.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStats();
  }, []);

  return {
    stats,
    loading,
    error,
    reload: loadStats,
  };
};


