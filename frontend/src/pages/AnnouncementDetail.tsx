import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Paper,
  Button,
  Divider,
  Chip,
  Grid,
  Card,
  CardContent,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Menu,
  MenuItem,
  IconButton,
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import CancelIcon from '@mui/icons-material/Cancel';
import DeleteIcon from '@mui/icons-material/Delete';
import { getAnnouncementById, updateAnnouncementStatus, deleteAnnouncement } from '../services/api';
import { Announcement } from '../types';
import { formatBudget, formatDateShort, getNaraJangteoUrl } from '../utils/formatters';
import LoadingSpinner from '../components/LoadingSpinner';

const AnnouncementDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [announcement, setAnnouncement] = useState<Announcement | null>(null);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [menuAnchor, setMenuAnchor] = useState<null | HTMLElement>(null);

  useEffect(() => {
    if (id) {
      loadAnnouncement(id);
    }
  }, [id]);

  const loadAnnouncement = async (announcementId: string) => {
    try {
      setLoading(true);
      const response = await getAnnouncementById(announcementId);
      if (response.success && response.data) {
        setAnnouncement(response.data);
      }
    } catch (error) {
      console.error('공고 상세 정보 로드 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleStatusChange = async (newStatus: 'approved' | 'rejected') => {
    if (!id || !announcement) return;

    try {
      setUpdating(true);
      const response = await updateAnnouncementStatus(id, newStatus);
      
      if (response.success) {
        // 로컬 상태 업데이트
        setAnnouncement({
          ...announcement,
          status: newStatus,
          reviewed: true,
        });
        setMenuAnchor(null);
      } else {
        alert(response.error || '상태 변경에 실패했습니다.');
      }
    } catch (error) {
      console.error('상태 변경 실패:', error);
      alert('상태 변경 중 오류가 발생했습니다.');
    } finally {
      setUpdating(false);
    }
  };

  const handleDeleteClick = () => {
    setMenuAnchor(null);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!id) return;

    try {
      setUpdating(true);
      const response = await deleteAnnouncement(id);
      
      if (response.success) {
        alert('공고가 삭제되었습니다.');
        navigate('/announcements');
      } else {
        alert(response.error || '삭제에 실패했습니다.');
      }
    } catch (error) {
      console.error('삭제 실패:', error);
      alert('삭제 중 오류가 발생했습니다.');
    } finally {
      setUpdating(false);
      setDeleteDialogOpen(false);
    }
  };

  if (loading) {
    return <LoadingSpinner />;
  }

  if (!announcement) {
    return (
      <Box>
        <Typography variant="h6">공고를 찾을 수 없습니다.</Typography>
        <Button onClick={() => navigate('/announcements')}>목록으로</Button>
      </Box>
    );
  }

  return (
    <Box>
      <Button
        startIcon={<ArrowBackIcon />}
        onClick={() => navigate('/announcements')}
        sx={{ mb: 2 }}
      >
        목록으로
      </Button>

      <Paper sx={{ p: 3 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h4" component="h1">
            {announcement.title || '제목 없음'}
          </Typography>
          <Box display="flex" gap={2} alignItems="center">
            <Chip
              label={announcement.status === 'approved' ? '적합' : '부적합'}
              color={announcement.status === 'approved' ? 'success' : 'error'}
              size="medium"
            />
            {(() => {
              const naraUrl = getNaraJangteoUrl(announcement.announcement_number);
              return naraUrl ? (
                <Button
                  variant="contained"
                  color="primary"
                  startIcon={<OpenInNewIcon />}
                  href={naraUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  component="a"
                >
                  나라장터에서 보기
                </Button>
              ) : null;
            })()}
            <IconButton
              onClick={(e) => setMenuAnchor(e.currentTarget)}
              disabled={updating}
            >
              <MoreVertIcon />
            </IconButton>
            <Menu
              anchorEl={menuAnchor}
              open={Boolean(menuAnchor)}
              onClose={() => setMenuAnchor(null)}
            >
              {announcement.status !== 'approved' && (
                <MenuItem
                  onClick={() => handleStatusChange('approved')}
                  disabled={updating}
                >
                  <CheckCircleIcon sx={{ mr: 1, color: 'success.main' }} />
                  적합으로 변경
                </MenuItem>
              )}
              {announcement.status !== 'rejected' && (
                <MenuItem
                  onClick={() => handleStatusChange('rejected')}
                  disabled={updating}
                >
                  <CancelIcon sx={{ mr: 1, color: 'error.main' }} />
                  부적합으로 변경
                </MenuItem>
              )}
              <Divider />
              <MenuItem
                onClick={handleDeleteClick}
                disabled={updating}
                sx={{ color: 'error.main' }}
              >
                <DeleteIcon sx={{ mr: 1 }} />
                삭제
              </MenuItem>
            </Menu>
          </Box>
        </Box>

        <Divider sx={{ my: 2 }} />

        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle2" color="textSecondary">
            공고번호
          </Typography>
          <Typography variant="body1">{announcement.announcement_number || '-'}</Typography>
        </Box>

        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle2" color="textSecondary">
            기관
          </Typography>
          <Typography variant="body1">{announcement.agency || '-'}</Typography>
        </Box>

        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle2" color="textSecondary">
            사업구분
          </Typography>
          <Typography variant="body1">{announcement.business_type || '-'}</Typography>
        </Box>

        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle2" color="textSecondary">
            공고상태
          </Typography>
          <Typography variant="body1">{announcement.announcement_status || '-'}</Typography>
        </Box>

        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle2" color="textSecondary">
            예산금액
          </Typography>
          <Typography variant="body1">
            {formatBudget(announcement.budget_amount)}
          </Typography>
        </Box>

        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle2" color="textSecondary">
            추정가격
          </Typography>
          <Typography variant="body1">
            {formatBudget(announcement.estimated_price)}
          </Typography>
        </Box>

        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle2" color="textSecondary">
            마감일
          </Typography>
          <Typography variant="body1">{announcement.deadline || '-'}</Typography>
        </Box>

        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle2" color="textSecondary">
            카테고리
          </Typography>
          <Typography variant="body1">{announcement.category || '-'}</Typography>
        </Box>

        {announcement.url && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle2" color="textSecondary">
              원본 링크
            </Typography>
            <Typography variant="body1">
              <a href={announcement.url} target="_blank" rel="noopener noreferrer">
                {announcement.url}
              </a>
            </Typography>
          </Box>
        )}

        <Divider sx={{ my: 2 }} />

        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle2" color="textSecondary" gutterBottom>
            내용
          </Typography>
          <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
            {announcement.content || '내용 없음'}
          </Typography>
        </Box>

        {announcement.review_result && (
          <>
            <Divider sx={{ my: 2 }} />
            <Box>
              <Typography variant="subtitle2" color="textSecondary" gutterBottom>
                검수 결과
              </Typography>
              <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                  {announcement.review_result}
                </Typography>
              </Paper>
            </Box>
          </>
        )}

        {announcement.service_items && announcement.service_items.length > 0 && (
          <>
            <Divider sx={{ my: 2 }} />
            <Box>
              <Typography variant="h6" gutterBottom>
                요구 서비스 항목
              </Typography>
              <Typography variant="caption" color="textSecondary" sx={{ mb: 2, display: 'block' }}>
                {announcement.service_items_extracted_at 
                  ? `추출일시: ${new Date(announcement.service_items_extracted_at).toLocaleString('ko-KR')}`
                  : '이 공고에서 요구하는 서비스 항목 목록입니다.'}
              </Typography>
              <Grid container spacing={2}>
                {announcement.service_items.map((item, index) => (
                  <Grid item xs={12} sm={6} md={4} key={index}>
                    <Card
                      sx={{
                        height: '100%',
                        display: 'flex',
                        flexDirection: 'column',
                        border: '1px solid',
                        borderColor: 'divider',
                        '&:hover': {
                          boxShadow: 2,
                          borderColor: 'primary.main',
                        },
                        transition: 'all 0.2s ease-in-out',
                      }}
                    >
                      <CardContent sx={{ flexGrow: 1 }}>
                        <Typography 
                          variant="subtitle1" 
                          fontWeight="medium" 
                          gutterBottom
                          sx={{ mb: 1 }}
                        >
                          {item.구분}
                        </Typography>
                        <Typography 
                          variant="body2" 
                          color="text.secondary"
                          sx={{ 
                            lineHeight: 1.6,
                            display: '-webkit-box',
                            WebkitLineClamp: 3,
                            WebkitBoxOrient: 'vertical',
                            overflow: 'hidden',
                          }}
                        >
                          {item.설명}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            </Box>
          </>
        )}

        <Box sx={{ mt: 3 }}>
          <Typography variant="caption" color="textSecondary">
            수집일: {new Date(announcement.created_at).toLocaleString('ko-KR')}
          </Typography>
        </Box>
      </Paper>

      {/* 삭제 확인 다이얼로그 */}
      <Dialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
      >
        <DialogTitle>공고 삭제 확인</DialogTitle>
        <DialogContent>
          <DialogContentText>
            정말로 이 공고를 삭제하시겠습니까?
            <br />
            <strong>{announcement.title}</strong>
            <br />
            <br />
            공고는 숨김 처리되며, 목록에서 보이지 않게 됩니다.
            <br />
            실수로 삭제한 경우, DB에서 display_status를 20으로 변경하면 다시 표시됩니다.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)} disabled={updating}>
            취소
          </Button>
          <Button
            onClick={handleDeleteConfirm}
            color="error"
            variant="contained"
            disabled={updating}
            startIcon={<DeleteIcon />}
          >
            삭제
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AnnouncementDetail;

