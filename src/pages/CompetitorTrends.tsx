import React, { useState, useMemo } from 'react';
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
  TextField,
  InputAdornment,
  Button,
  Menu,
  MenuItem,
  Chip,
} from '@mui/material';
import { Search, Sort } from '@mui/icons-material';
import { useCompetitorAwards } from '../hooks/useCompetitorAwards';
import { formatBudget, formatDateShort } from '../utils/formatters';
import LoadingSpinner from '../components/LoadingSpinner';

const CompetitorTrends: React.FC = () => {
  const { awards, loading, error } = useCompetitorAwards({ limit: 100 });
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState<'publish_date' | 'created_at' | 'final_amount'>('publish_date');
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const filteredAwards = awards
    .filter((award) => {
      const matchesSearch =
        (award.title || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
        (award.agency || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
        (award.winner || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
        (award.announcement_number || '').toLowerCase().includes(searchTerm.toLowerCase());
      
      return matchesSearch;
    })
    .sort((a, b) => {
      if (sortBy === 'publish_date') {
        const dateA = a.publish_date ? new Date(a.publish_date.replace(/\//g, '-')).getTime() : 0;
        const dateB = b.publish_date ? new Date(b.publish_date.replace(/\//g, '-')).getTime() : 0;
        return dateB - dateA; // 최신순
      } else if (sortBy === 'created_at') {
        return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      } else {
        const amountA = a.final_amount || 0;
        const amountB = b.final_amount || 0;
        return amountB - amountA;
      }
    });

  const handleSortMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleSortMenuClose = () => {
    setAnchorEl(null);
  };

  const formatAmount = (value: any): string => {
    if (!value) return '-';
    const num = Number(value);
    if (!num || Number.isNaN(num)) return '-';
    return num.toLocaleString('ko-KR') + '원';
  };

  if (loading) {
    return <LoadingSpinner />;
  }

  if (error) {
    return (
      <Box>
        <Typography variant="h4" component="h1" fontWeight="bold" mb={3}>
          경쟁사 동향
        </Typography>
        <Paper sx={{ p: 3 }}>
          <Typography color="error">{error}</Typography>
        </Paper>
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1" fontWeight="bold">
          경쟁사 동향
        </Typography>
        <Box display="flex" gap={2} alignItems="center">
          <TextField
            placeholder="제목, 기관, 낙찰자, 공고번호 검색..."
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
              낙찰일순
            </MenuItem>
            <MenuItem onClick={() => { setSortBy('created_at'); handleSortMenuClose(); }}>
              수집일순
            </MenuItem>
            <MenuItem onClick={() => { setSortBy('final_amount'); handleSortMenuClose(); }}>
              낙찰금액순
            </MenuItem>
          </Menu>
        </Box>
      </Box>

      <Typography variant="body2" color="textSecondary" mb={2}>
        총 {filteredAwards.length}건의 경쟁사 낙찰정보
      </Typography>

      <TableContainer component={Paper} elevation={2}>
        <Table>
          <TableHead>
            <TableRow sx={{ backgroundColor: 'grey.100' }}>
              <TableCell sx={{ fontWeight: 'bold' }}>공고번호</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>제목</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>기관</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>사업구분</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>낙찰자</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>낙찰금액</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>낙찰일</TableCell>
              <TableCell sx={{ fontWeight: 'bold' }}>수집일</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredAwards.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} align="center" sx={{ py: 4 }}>
                  <Typography color="textSecondary">
                    {searchTerm
                      ? '검색 조건에 맞는 낙찰정보가 없습니다.' 
                      : '낙찰정보가 없습니다.'}
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              filteredAwards.map((award) => (
                <TableRow 
                  key={award.id} 
                  hover
                  sx={{ 
                    '&:hover': { backgroundColor: 'action.hover' },
                  }}
                >
                  <TableCell>
                    <Typography variant="body2" color="primary" fontWeight="medium">
                      {award.announcement_number || '-'}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" fontWeight="medium" sx={{ maxWidth: 300 }}>
                      {award.title || '-'}
                    </Typography>
                  </TableCell>
                  <TableCell>{award.agency || '-'}</TableCell>
                  <TableCell>
                    <Chip 
                      label={award.business_type || '-'} 
                      size="small" 
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" fontWeight="medium">
                      {award.winner || '-'}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" fontWeight="medium" color="primary">
                      {formatAmount(award.final_amount)}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {award.publish_date || '-'}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" color="textSecondary">
                      {formatDateShort(award.created_at)}
                    </Typography>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default CompetitorTrends;
