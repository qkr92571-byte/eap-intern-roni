import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  TextField,
  InputAdornment,
  Card,
  CardContent,
  Grid,
  Tabs,
  Tab,
  Button,
  Menu,
  MenuItem,
  Stack,
  Divider,
} from '@mui/material';
import {
  Search,
  Visibility,
  Sort,
  ViewList,
  ViewModule,
} from '@mui/icons-material';
import { useAnnouncements } from '../hooks/useAnnouncements';
import { Announcement, AnnouncementStatus } from '../types';
import { STATUS_LABELS, STATUS_COLORS, ANNOUNCEMENT_STATUS } from '../utils/constants';
import { formatBudget, formatDateShort } from '../utils/formatters';
import StatusChip from '../components/StatusChip';
import LoadingSpinner from '../components/LoadingSpinner';

const AnnouncementList: React.FC = () => {
  const { announcements, loading } = useAnnouncements({ limit: 100 });
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [viewMode, setViewMode] = useState<'table' | 'card'>('table');
  const [sortBy, setSortBy] = useState<'date' | 'budget'>('date');
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const navigate = useNavigate();

  const filteredAnnouncements = announcements
    .filter((announcement) => {
      const matchesSearch =
        announcement.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        announcement.agency.toLowerCase().includes(searchTerm.toLowerCase()) ||
        announcement.announcement_number?.toLowerCase().includes(searchTerm.toLowerCase());
      
      const matchesStatus = statusFilter === 'all' || announcement.status === statusFilter;
      
      return matchesSearch && matchesStatus;
    })
    .sort((a, b) => {
      if (sortBy === 'date') {
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      } else {
        const budgetA = a.budget_amount || 0;
        const budgetB = b.budget_amount || 0;
        return budgetB - budgetA;
      }
    });

  // 상태별 공고 개수 계산
  const statusCounts = useMemo(() => {
    return {
      all: announcements.length,
      pending: announcements.filter(a => a.status === ANNOUNCEMENT_STATUS.PENDING).length,
      approved: announcements.filter(a => a.status === ANNOUNCEMENT_STATUS.APPROVED).length,
      rejected: announcements.filter(a => a.status === ANNOUNCEMENT_STATUS.REJECTED).length,
    };
  }, [announcements]);

  const handleSortMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleSortMenuClose = () => {
    setAnchorEl(null);
  };

  if (loading) {
    return <LoadingSpinner />;
  }

  return (
    <Box>
      {/* 헤더 섹션 */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1" fontWeight="bold">
          공고 목록
        </Typography>
        <Box display="flex" gap={2} alignItems="center">
          <TextField
            placeholder="제목, 기관, 공고번호 검색..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <Search />
                </InputAdornment>
              ),
            }}
            sx={{ width: 300 }}
            size="small"
          />
          <Button
            variant="outlined"
            startIcon={<Sort />}
            onClick={handleSortMenuOpen}
            size="small"
          >
            정렬
          </Button>
          <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={handleSortMenuClose}>
            <MenuItem onClick={() => { setSortBy('date'); handleSortMenuClose(); }}>
              수집일순
            </MenuItem>
            <MenuItem onClick={() => { setSortBy('budget'); handleSortMenuClose(); }}>
              예산순
            </MenuItem>
          </Menu>
          <IconButton
            onClick={() => setViewMode(viewMode === 'table' ? 'card' : 'table')}
            color={viewMode === 'table' ? 'primary' : 'default'}
          >
            {viewMode === 'table' ? <ViewModule /> : <ViewList />}
          </IconButton>
        </Box>
      </Box>

      {/* 상태 필터 탭 */}
      <Tabs
        value={statusFilter}
        onChange={(e, newValue) => setStatusFilter(newValue)}
        sx={{ mb: 3, borderBottom: 1, borderColor: 'divider' }}
      >
        <Tab label={`전체 (${statusCounts.all})`} value="all" />
        <Tab label={`대기 중 (${statusCounts.pending})`} value="pending" />
        <Tab label={`승인됨 (${statusCounts.approved})`} value="approved" />
        <Tab label={`거부됨 (${statusCounts.rejected})`} value="rejected" />
      </Tabs>

      {/* 테이블 뷰 */}
      {viewMode === 'table' && (
        <TableContainer component={Paper} elevation={2}>
          <Table>
            <TableHead>
              <TableRow sx={{ backgroundColor: 'grey.100' }}>
                <TableCell sx={{ fontWeight: 'bold' }}>공고번호</TableCell>
                <TableCell sx={{ fontWeight: 'bold' }}>제목</TableCell>
                <TableCell sx={{ fontWeight: 'bold' }}>기관</TableCell>
                <TableCell sx={{ fontWeight: 'bold' }}>사업구분</TableCell>
                <TableCell sx={{ fontWeight: 'bold' }}>예산금액</TableCell>
                <TableCell sx={{ fontWeight: 'bold' }}>마감일</TableCell>
                <TableCell sx={{ fontWeight: 'bold' }}>상태</TableCell>
                <TableCell sx={{ fontWeight: 'bold' }}>수집일</TableCell>
                <TableCell sx={{ fontWeight: 'bold' }}>작업</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredAnnouncements.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={9} align="center" sx={{ py: 4 }}>
                    <Typography color="textSecondary">
                      {searchTerm || statusFilter !== 'all' 
                        ? '검색 조건에 맞는 공고가 없습니다.' 
                        : '공고가 없습니다.'}
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                filteredAnnouncements.map((announcement) => (
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
                      <Typography variant="body2" fontWeight="medium" color="primary">
                        {formatBudget(announcement.budget_amount)}
                      </Typography>
                    </TableCell>
                    <TableCell>{announcement.deadline || '-'}</TableCell>
                    <TableCell>
                      <StatusChip status={announcement.status as AnnouncementStatus} />
                    </TableCell>
                    <TableCell>
                      <Typography variant="caption" color="textSecondary">
                        {formatDateShort(announcement.created_at)}
                      </Typography>
                    </TableCell>
                    <TableCell onClick={(e) => e.stopPropagation()}>
                      <IconButton
                        size="small"
                        onClick={() => navigate(`/announcements/${announcement.id}`)}
                        color="primary"
                      >
                        <Visibility />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* 카드 뷰 */}
      {viewMode === 'card' && (
        <Grid container spacing={3}>
          {filteredAnnouncements.length === 0 ? (
            <Grid item xs={12}>
              <Paper sx={{ p: 4, textAlign: 'center' }}>
                <Typography color="textSecondary">
                  {searchTerm || statusFilter !== 'all' 
                    ? '검색 조건에 맞는 공고가 없습니다.' 
                    : '공고가 없습니다.'}
                </Typography>
              </Paper>
            </Grid>
          ) : (
            filteredAnnouncements.map((announcement) => (
              <Grid item xs={12} md={6} lg={4} key={announcement.id}>
                <Card 
                  elevation={2}
                  sx={{ 
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                    transition: 'transform 0.2s, box-shadow 0.2s',
                    '&:hover': {
                      transform: 'translateY(-4px)',
                      boxShadow: 4,
                      cursor: 'pointer'
                    }
                  }}
                  onClick={() => navigate(`/announcements/${announcement.id}`)}
                >
                  <CardContent sx={{ flexGrow: 1 }}>
                    <Box display="flex" justifyContent="space-between" alignItems="start" mb={1}>
                      <StatusChip status={announcement.status as AnnouncementStatus} />
                      <Typography variant="caption" color="textSecondary">
                        {formatDateShort(announcement.created_at)}
                      </Typography>
                    </Box>
                    
                    <Typography 
                      variant="h6" 
                      component="h3" 
                      gutterBottom
                      sx={{ 
                        fontWeight: 'bold',
                        mb: 1,
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        display: '-webkit-box',
                        WebkitLineClamp: 2,
                        WebkitBoxOrient: 'vertical'
                      }}
                    >
                      {announcement.title || '제목 없음'}
                    </Typography>
                    
                    <Typography variant="body2" color="primary" fontWeight="medium" mb={1}>
                      {announcement.announcement_number || '-'}
                    </Typography>
                    
                    <Divider sx={{ my: 1.5 }} />
                    
                    <Stack spacing={1}>
                      <Box display="flex" justifyContent="space-between">
                        <Typography variant="caption" color="textSecondary">기관</Typography>
                        <Typography variant="body2" fontWeight="medium">
                          {announcement.agency || '-'}
                        </Typography>
                      </Box>
                      
                      {announcement.business_type && (
                        <Box display="flex" justifyContent="space-between">
                          <Typography variant="caption" color="textSecondary">사업구분</Typography>
                          <Chip label={announcement.business_type} size="small" variant="outlined" />
                        </Box>
                      )}
                      
                      {announcement.budget_amount && (
                        <Box display="flex" justifyContent="space-between">
                          <Typography variant="caption" color="textSecondary">예산금액</Typography>
                          <Typography variant="body2" fontWeight="bold" color="primary">
                            {formatBudget(announcement.budget_amount)}
                          </Typography>
                        </Box>
                      )}
                      
                      {announcement.deadline && (
                        <Box display="flex" justifyContent="space-between">
                          <Typography variant="caption" color="textSecondary">마감일</Typography>
                          <Typography variant="body2">{announcement.deadline}</Typography>
                        </Box>
                      )}
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>
            ))
          )}
        </Grid>
      )}

      {/* 결과 카운트 */}
      {filteredAnnouncements.length > 0 && (
        <Box mt={3} textAlign="center">
          <Typography variant="body2" color="textSecondary">
            총 {filteredAnnouncements.length}개의 공고가 표시됩니다.
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default AnnouncementList;

