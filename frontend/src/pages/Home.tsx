import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  CircularProgress,
  Alert,
  Button,
} from '@mui/material';
import {
  Article as ArticleIcon,
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
} from '@mui/icons-material';
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  LineChart,
  Line,
  ResponsiveContainer,
} from 'recharts';
import useDashboard from '../hooks/useDashboard';
import { AnnouncementStatus } from '../types';

/** 상태별 Chip 색상 */
const statusConfig: Record<AnnouncementStatus, { label: string; color: 'success' | 'error' }> = {
  approved: { label: '적합', color: 'success' },
  rejected: { label: '부적합', color: 'error' },
};

/** 통계 카드 설정 */
const statCards = [
  { key: 'total' as const, label: '총 공고', color: '#1976d2', icon: <ArticleIcon /> },
  { key: 'approved' as const, label: '적합', color: '#2e7d32', icon: <CheckCircleIcon /> },
  { key: 'rejected' as const, label: '부적합', color: '#d32f2f', icon: <CancelIcon /> },
];


const Home: React.FC = () => {
  const { stats, recentAnnouncements, agencyTopFive, dailyTrend, loading, error } = useDashboard();
  const navigate = useNavigate();
  const [recentFilter, setRecentFilter] = useState<'approved' | 'rejected'>('approved');

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  // 도넛 차트 데이터
  const pieData = [
    { name: '적합', value: stats.approved, color: '#2e7d32' },
    { name: '부적합', value: stats.rejected, color: '#d32f2f' },
  ].filter((d) => d.value > 0);

  return (
    <Box>
      <Typography variant="h5" sx={{ mb: 3, fontWeight: 'bold' }}>
        대시보드
      </Typography>

      {/* Row 1: 통계 카드 4개 */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        {statCards.map((card) => (
          <Grid item xs={6} sm={3} key={card.key}>
            <Card
              sx={{ borderLeft: `4px solid ${card.color}`, height: '100%', cursor: card.key !== 'total' ? 'pointer' : 'default', '&:hover': card.key !== 'total' ? { boxShadow: 4 } : {} }}
              onClick={() => { if (card.key !== 'total') setRecentFilter(card.key as 'approved' | 'rejected'); }}
            >
              <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Box sx={{ color: card.color }}>{card.icon}</Box>
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 'bold', color: card.color, lineHeight: 1 }}>
                    {stats[card.key]}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {card.label}
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Row 2: 도넛 차트 + 최근 공고 테이블 */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        {/* 좌: 검수 현황 도넛 차트 */}
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 1, fontWeight: 'bold' }}>
                검수 현황
              </Typography>
              {stats.total === 0 ? (
                <Typography variant="body2" color="text.secondary">데이터가 없습니다.</Typography>
              ) : (
                <ResponsiveContainer width="100%" height={220}>
                  <PieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={85}
                      dataKey="value"
                    >
                      {pieData.map((entry, index) => (
                        <Cell key={index} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value) => `${value ?? 0}건`} />
                    <Legend />
                    {/* 중앙 총 건수 */}
                    <text x="50%" y="43%" textAnchor="middle" fill="#333" fontSize={22} fontWeight="bold" dominantBaseline="middle">
                      {stats.total}
                    </text>
                    <text x="50%" y="55%" textAnchor="middle" fill="#888" fontSize={12} dominantBaseline="middle">
                      전체
                    </text>
                  </PieChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* 우: 최근 공고 테이블 (필터별 5건) */}
        <Grid item xs={12} md={8}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1.5 }}>
                <Typography variant="h6" sx={{ fontWeight: 'bold' }}>최근 공고</Typography>
                <Box sx={{ display: 'flex', gap: 0.5 }}>
                  {(['approved', 'rejected'] as const).map((f) => {
                    const cfg = statusConfig[f];
                    return (
                      <Button
                        key={f}
                        size="small"
                        variant={recentFilter === f ? 'contained' : 'outlined'}
                        color={cfg.color}
                        onClick={() => setRecentFilter(f)}
                        sx={{ minWidth: 0, px: 1.2, py: 0.3, fontSize: 12 }}
                      >
                        {cfg.label}
                      </Button>
                    );
                  })}
                </Box>
              </Box>
              {(() => {
                const filtered = recentAnnouncements.filter((a) => a.status === recentFilter).slice(0, 5);
                return (
                  <TableContainer component={Paper} variant="outlined">
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>제목</TableCell>
                          <TableCell>발주기관</TableCell>
                          <TableCell>수집일</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {filtered.map((a) => (
                          <TableRow
                            key={a.id}
                            hover
                            sx={{ cursor: 'pointer' }}
                            onClick={() => navigate(`/announcements/${a.id}`)}
                          >
                            <TableCell sx={{ maxWidth: 260, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                              {a.title}
                            </TableCell>
                            <TableCell>{a.agency}</TableCell>
                            <TableCell>
                              {a.created_at ? new Date(a.created_at).toLocaleDateString('ko-KR') : '-'}
                            </TableCell>
                          </TableRow>
                        ))}
                        {filtered.length === 0 && (
                          <TableRow>
                            <TableCell colSpan={3} align="center">공고가 없습니다.</TableCell>
                          </TableRow>
                        )}
                      </TableBody>
                    </Table>
                  </TableContainer>
                );
              })()}
              <Box sx={{ mt: 1, textAlign: 'right' }}>
                <Button size="small" onClick={() => navigate(`/announcements?filter=${recentFilter}`)}>
                  전체 보기 →
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Row 3: 기관별 Top5 바차트 + 최근 7일 추이 라인차트 */}
      <Grid container spacing={2}>
        {/* 좌: 기관별 Top5 수평 바차트 */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 1, fontWeight: 'bold' }}>
                기관별 공고 Top 5
              </Typography>
              {agencyTopFive.length === 0 ? (
                <Typography variant="body2" color="text.secondary">데이터가 없습니다.</Typography>
              ) : (
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={agencyTopFive} layout="vertical" margin={{ left: 10, right: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                    <XAxis type="number" allowDecimals={false} />
                    <YAxis type="category" dataKey="agency" width={120} tick={{ fontSize: 12 }} />
                    <Tooltip formatter={(value) => `${value ?? 0}건`} />
                    <Bar dataKey="count" fill="#1976d2" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* 우: 최근 7일 수집 추이 라인차트 */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 1, fontWeight: 'bold' }}>
                최근 7일 수집 추이
              </Typography>
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={dailyTrend} margin={{ left: 0, right: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                  <YAxis allowDecimals={false} />
                  <Tooltip formatter={(value) => `${value ?? 0}건`} />
                  <Line type="monotone" dataKey="count" stroke="#1976d2" strokeWidth={2} dot={{ r: 4 }} activeDot={{ r: 6 }} />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Home;
