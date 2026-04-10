import { useState, useEffect } from 'react';
import { getAnnouncements } from '../services/api';
import { Announcement, Stats } from '../types';

interface AgencyCount {
  agency: string;
  count: number;
}

interface DailyCount {
  date: string;
  count: number;
}

interface DashboardData {
  stats: Stats;
  recentAnnouncements: Announcement[];
  agencyTopFive: AgencyCount[];
  dailyTrend: DailyCount[];
  loading: boolean;
  error: string | null;
}

/**
 * 홈 대시보드용 훅
 * getAnnouncements로 한 번만 쿼리하여 통계, 최근 공고, 기관별 Top5를 계산
 */
const useDashboard = (): DashboardData => {
  const [stats, setStats] = useState<Stats>({ total: 0, approved: 0, rejected: 0 });
  const [recentAnnouncements, setRecentAnnouncements] = useState<Announcement[]>([]);
  const [agencyTopFive, setAgencyTopFive] = useState<AgencyCount[]>([]);
  const [dailyTrend, setDailyTrend] = useState<DailyCount[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await getAnnouncements();

        if (!response.success || !response.data) {
          setError(response.error || '데이터를 불러오는데 실패했습니다.');
          return;
        }

        const announcements = response.data;

        // 통계 계산
        const total = announcements.length;
        const approved = announcements.filter((a) => a.status === 'approved').length;
        const rejected = announcements.filter((a) => a.status === 'rejected').length;
        setStats({ total, approved, rejected });

        // 전체 공고 전달 (Home에서 필터링 후 5건 표시)
        setRecentAnnouncements(announcements);

        // 기관별 그룹핑 → 상위 5개
        const agencyMap: Record<string, number> = {};
        announcements.forEach((a) => {
          const agency = a.agency || '기관 미상';
          agencyMap[agency] = (agencyMap[agency] || 0) + 1;
        });
        const sorted = Object.entries(agencyMap)
          .map(([agency, count]) => ({ agency, count }))
          .sort((a, b) => b.count - a.count)
          .slice(0, 5);
        setAgencyTopFive(sorted);

        // 최근 7일 일별 수집 추이 (KST 기준)
        const KST_OFFSET = 9 * 60 * 60 * 1000; // UTC+9
        // UTC 시각에 +9h 해서 KST 날짜 문자열(YYYY-MM-DD) 추출
        const toKstDateStr = (date: Date) =>
          new Date(date.getTime() + KST_OFFSET).toISOString().slice(0, 10);

        const today = new Date();
        const trend: DailyCount[] = [];
        for (let i = 6; i >= 0; i--) {
          const d = new Date(today);
          d.setDate(d.getDate() - i);
          const kstDateStr = toKstDateStr(d);
          // 표시용 날짜: KST 기준 MM/DD
          const [, mm, dd] = kstDateStr.split('-');
          const dateStr = `${mm}/${dd}`;
          const count = announcements.filter((a) => {
            if (!a.created_at) return false;
            return toKstDateStr(new Date(a.created_at)) === kstDateStr;
          }).length;
          trend.push({ date: dateStr, count });
        }
        setDailyTrend(trend);
      } catch (err: any) {
        setError(err.message || '대시보드 데이터를 불러오는데 실패했습니다.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return { stats, recentAnnouncements, agencyTopFive, dailyTrend, loading, error };
};

export default useDashboard;
