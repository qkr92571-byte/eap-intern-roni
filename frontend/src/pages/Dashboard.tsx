import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Button,
} from '@mui/material';
import {
  Announcement,
  CheckCircle,
  Pending,
  Block,
  ArrowForward,
} from '@mui/icons-material';
import { useStats } from '../hooks/useStats';
import { useAnnouncements } from '../hooks/useAnnouncements';
import { formatBudget } from '../utils/formatters';
import StatusChip from '../components/StatusChip';
import LoadingSpinner from '../components/LoadingSpinner';

const Dashboard: React.FC = () => {
  const { stats, loading: statsLoading } = useStats();
  const { announcements, loading: announcementsLoading } = useAnnouncements({ limit: 10 });
  const navigate = useNavigate();

  const statCards = [
    {
      title: '전체 공고',
      value: stats.total,
      icon: <Announcement sx={{ fontSize: 40 }} />,
      color: '#1976d2',
    },
    {
      title: '승인됨',
      value: stats.approved,
      icon: <CheckCircle sx={{ fontSize: 40 }} />,
      color: '#2e7d32',
    },
    {
      title: '대기 중',
      value: stats.pending,
      icon: <Pending sx={{ fontSize: 40 }} />,
      color: '#ed6c02',
    },
    {
      title: '거부됨',
      value: stats.rejected,
      icon: <Block sx={{ fontSize: 40 }} />,
      color: '#d32f2f',
    },
  ];

  if (statsLoading || announcementsLoading) {
    return <LoadingSpinner />;
  }

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        대시보드
      </Typography>
      
      {/* 통계 카드 */}
      <Grid container spacing={3} sx={{ mt: 2 }}>
        {statCards.map((card, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" justifyContent="space-between">
                  <Box>
                    <Typography color="textSecondary" gutterBottom>
                      {card.title}
                    </Typography>
                    <Typography variant="h4" component="div" sx={{ color: card.color }}>
                      {card.value}
                    </Typography>
                  </Box>
                  <Box sx={{ color: card.color }}>{card.icon}</Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* 최근 공고 목록 */}
      <Box sx={{ mt: 4 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h5" component="h2" fontWeight="bold">
            최근 공고 목록
          </Typography>
          <Button
            variant="outlined"
            endIcon={<ArrowForward />}
            onClick={() => navigate('/announcements')}
          >
            전체 보기
          </Button>
        </Box>
        
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>공고번호</TableCell>
                <TableCell>공고명</TableCell>
                <TableCell>기관</TableCell>
                <TableCell>업무구분</TableCell>
                <TableCell>게시일</TableCell>
                <TableCell>예산금액</TableCell>
                <TableCell>상태</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {announcements.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} align="center" sx={{ py: 4 }}>
                    <Typography color="textSecondary">
                      공고가 없습니다.
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                announcements.map((announcement) => (
                  <TableRow
                    key={announcement.id}
                    hover
                    sx={{
                      '&:hover': { backgroundColor: 'action.hover' },
                      cursor: 'pointer'
                    }}
                    onClick={() => navigate(`/announcements/${announcement.id}`)}
                  >
                    <TableCell>
                      <Typography variant="body2" color="primary" fontWeight="medium">
                        {announcement.announcement_number || '-'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" fontWeight="medium" sx={{ maxWidth: 300 }}>
                        {announcement.title || '-'}
                      </Typography>
                    </TableCell>
                    <TableCell>{announcement.agency || '-'}</TableCell>
                    <TableCell>
                      <Chip
                        label={announcement.business_type || '-'}
                        size="small"
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {announcement.publish_date || '-'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {announcement.budget_amount
                          ? formatBudget(announcement.budget_amount)
                          : '-'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <StatusChip status={announcement.status} />
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Box>
    </Box>
  );
};

export default Dashboard;

