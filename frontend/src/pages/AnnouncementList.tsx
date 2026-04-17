import React, { useState, useMemo } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
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
  TextField,
  InputAdornment,
  Button,
  Menu,
  MenuItem,
  Tabs,
  Tab,
  Pagination,
} from '@mui/material';
import {
  Search,
  Sort,
} from '@mui/icons-material';
import { useAnnouncements } from '../hooks/useAnnouncements';
import { Announcement } from '../types';
import { formatBudget, formatDateShort } from '../utils/formatters';
import LoadingSpinner from '../components/LoadingSpinner';

const ITEMS_PER_PAGE = 50;

const AnnouncementList: React.FC = () => {
  const { announcements, loading } = useAnnouncements();
  const [searchParams] = useSearchParams();
  const [searchTerm, setSearchTerm] = useState('');
  const [reviewFilter, setReviewFilter] = useState<string>(searchParams.get('filter') || 'approved'); // 검수 결과 필터
  const [sortBy, setSortBy] = useState<'publish_date' | 'created_at' | 'budget'>('publish_date');
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [page, setPage] = useState(1);
  const navigate = useNavigate();

  const filteredAnnouncements = announcements
    .filter((announcement) => {
      const matchesSearch =
        announcement.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        announcement.agency.toLowerCase().includes(searchTerm.toLowerCase()) ||
        announcement.announcement_number?.toLowerCase().includes(searchTerm.toLowerCase());
      
      // 검수 결과 필터링 (적합/부적합)
      const matchesReview = (() => {
        if (reviewFilter === 'all') return true;
        if (reviewFilter === 'approved') return announcement.status === 'approved';
        if (reviewFilter === 'rejected') return announcement.status === 'rejected' || announcement.status === 'pending';
        
        return true;
      })();
      
      return matchesSearch && matchesReview;
    })
    .sort((a, b) => {
      if (sortBy === 'publish_date') {
        const dateA = a.publish_date ? new Date(a.publish_date).getTime() : 0;
        const dateB = b.publish_date ? new Date(b.publish_date).getTime() : 0;
        return dateB - dateA; // 최신순
      } else if (sortBy === 'created_at') {
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      } else {
        const budgetA = a.budget_amount || 0;
        const budgetB = b.budget_amount || 0;
        return budgetB - budgetA;
      }
    });

  // 페이지네이션 적용
  const paginatedAnnouncements = useMemo(() => {
    const start = (page - 1) * ITEMS_PER_PAGE;
    return filteredAnnouncements.slice(start, start + ITEMS_PER_PAGE);
  }, [filteredAnnouncements, page]);

  const totalPages = Math.ceil(filteredAnnouncements.length / ITEMS_PER_PAGE);

  // 검수 결과별 공고 개수 계산
  const reviewCounts = useMemo(() => {
    return {
      all: announcements.length,
      approved: announcements.filter(a => a.status === 'approved').length,
      rejected: announcements.filter(a => a.status === 'rejected' || a.status === 'pending').length,
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
            onChange={(e) => { setSearchTerm(e.target.value); setPage(1); }}
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
            <MenuItem onClick={() => { setSortBy('publish_date'); setPage(1); handleSortMenuClose(); }}>
              게시일순
            </MenuItem>
            <MenuItem onClick={() => { setSortBy('created_at'); setPage(1); handleSortMenuClose(); }}>
              수집일순
            </MenuItem>
            <MenuItem onClick={() => { setSortBy('budget'); setPage(1); handleSortMenuClose(); }}>
              예산순
            </MenuItem>
          </Menu>
        </Box>
      </Box>

      {/* 검수결과 필터 탭 */}
      <Tabs
        value={reviewFilter}
        onChange={(e, newValue) => { setReviewFilter(newValue); setPage(1); }}
        sx={{ mb: 3, borderBottom: 1, borderColor: 'divider' }}
      >
        <Tab label={`적합 (${reviewCounts.approved})`} value="approved" />
        <Tab label={`부적합 (${reviewCounts.rejected})`} value="rejected" />
      </Tabs>

      {/* 테이블 뷰 */}
      <TableContainer component={Paper} elevation={2}>
        <Table>
          <TableHead>
            <TableRow sx={{ backgroundColor: 'grey.100' }}>
              <TableCell sx={{ fontWeight: 'bold' }}>공고번호</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>제목</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>기관</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>사업구분</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>예산금액</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>게시일</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>마감일</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>검수결과</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>수집일</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredAnnouncements.length === 0 ? (
              <TableRow>
                <TableCell colSpan={9} align="center" sx={{ py: 4 }}>
                  <Typography color="textSecondary">
                    {searchTerm || reviewFilter
                      ? '검색 조건에 맞는 공고가 없습니다.' 
                      : '공고가 없습니다.'}
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              paginatedAnnouncements.map((announcement) => (
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
                  <TableCell>
                    <Typography variant="body2">
                      {announcement.publish_date || '-'}
                    </Typography>
                  </TableCell>
                  <TableCell>{announcement.deadline || '-'}</TableCell>
                  <TableCell>
                    <Chip
                      label={announcement.status === 'approved' ? '적합' : '부적합'}
                      color={announcement.status === 'approved' ? 'success' : 'error'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Typography variant="caption" color="textSecondary">
                      {formatDateShort(announcement.created_at)}
                    </Typography>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* 페이지네이션 */}
      {filteredAnnouncements.length > 0 && (
        <Box mt={3} display="flex" flexDirection="column" alignItems="center" gap={1}>
          <Typography variant="body2" color="textSecondary">
            {(page - 1) * ITEMS_PER_PAGE + 1}–{Math.min(page * ITEMS_PER_PAGE, filteredAnnouncements.length)} / 전체 {filteredAnnouncements.length}개
          </Typography>
          {totalPages > 1 && (
            <Pagination
              count={totalPages}
              page={page}
              onChange={(_, value) => { setPage(value); window.scrollTo({ top: 0, behavior: 'smooth' }); }}
              color="primary"
              showFirstButton
              showLastButton
            />
          )}
        </Box>
      )}
    </Box>
  );
};

export default AnnouncementList;

