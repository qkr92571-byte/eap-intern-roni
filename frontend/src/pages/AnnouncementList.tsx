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
  TextField,
  InputAdornment,
  Button,
  Menu,
  MenuItem,
  Tabs,
  Tab,
} from '@mui/material';
import {
  Search,
  Sort,
} from '@mui/icons-material';
import { useAnnouncements } from '../hooks/useAnnouncements';
import { Announcement } from '../types';
import { formatBudget, formatDateShort } from '../utils/formatters';
import LoadingSpinner from '../components/LoadingSpinner';

const AnnouncementList: React.FC = () => {
  const { announcements, loading } = useAnnouncements({ limit: 100 });
  const [searchTerm, setSearchTerm] = useState('');
  const [reviewFilter, setReviewFilter] = useState<string>('approved'); // 검수 결과 필터
  const [sortBy, setSortBy] = useState<'publish_date' | 'created_at' | 'budget'>('publish_date');
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
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
        if (reviewFilter === 'rejected') return announcement.status === 'rejected';
        if (reviewFilter === 'pending') return announcement.status === 'pending' || !announcement.reviewed;
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

  // 검수 결과별 공고 개수 계산
  const reviewCounts = useMemo(() => {
    return {
      all: announcements.length,
      approved: announcements.filter(a => a.status === 'approved').length,
      rejected: announcements.filter(a => a.status === 'rejected').length,
      pending: announcements.filter(a => a.status === 'pending' || !a.reviewed).length,
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
            <MenuItem onClick={() => { setSortBy('publish_date'); handleSortMenuClose(); }}>
              게시일순
            </MenuItem>
            <MenuItem onClick={() => { setSortBy('created_at'); handleSortMenuClose(); }}>
              수집일순
            </MenuItem>
            <MenuItem onClick={() => { setSortBy('budget'); handleSortMenuClose(); }}>
              예산순
            </MenuItem>
          </Menu>
        </Box>
      </Box>

      {/* 검수결과 필터 탭 */}
      <Tabs
        value={reviewFilter}
        onChange={(e, newValue) => setReviewFilter(newValue)}
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
                  <TableCell>
                    <Typography variant="body2">
                      {announcement.publish_date || '-'}
                    </Typography>
                  </TableCell>
                  <TableCell>{announcement.deadline || '-'}</TableCell>
                  <TableCell>
                    {announcement.reviewed ? (
                      <Chip
                        label={announcement.status === 'approved' ? '적합' : announcement.status === 'rejected' ? '부적합' : '미검수'}
                        color={announcement.status === 'approved' ? 'success' : announcement.status === 'rejected' ? 'error' : 'default'}
                        size="small"
                      />
                    ) : (
                      <Chip label="미검수" color="default" size="small" variant="outlined" />
                    )}
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

