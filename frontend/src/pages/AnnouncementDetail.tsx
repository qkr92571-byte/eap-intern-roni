import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Paper,
  Button,
  Divider,
  Chip,
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import { getAnnouncementById } from '../services/api';
import { Announcement } from '../types';
import { formatBudget, formatDateShort, getNaraJangteoUrl } from '../utils/formatters';
import LoadingSpinner from '../components/LoadingSpinner';

const AnnouncementDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [announcement, setAnnouncement] = useState<Announcement | null>(null);
  const [loading, setLoading] = useState(true);

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
            {(() => {
              // 검수 결과에 따른 뱃지 표시
              let reviewChip = null;
              if (announcement.reviewed) {
                if (announcement.status === 'approved') {
                  reviewChip = (
                    <Chip
                      label="적합"
                      color="success"
                      size="medium"
                    />
                  );
                } else if (announcement.status === 'rejected') {
                  reviewChip = (
                    <Chip
                      label="부적합"
                      color="error"
                      size="medium"
                    />
                  );
                } else {
                  reviewChip = (
                    <Chip
                      label="미검수"
                      color="default"
                      size="medium"
                      variant="outlined"
                    />
                  );
                }
              } else {
                reviewChip = (
                  <Chip
                    label="미검수"
                    color="default"
                    size="medium"
                    variant="outlined"
                  />
                );
              }
              return reviewChip;
            })()}
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

        <Box sx={{ mt: 3 }}>
          <Typography variant="caption" color="textSecondary">
            수집일: {new Date(announcement.created_at).toLocaleString('ko-KR')}
          </Typography>
        </Box>
      </Paper>
    </Box>
  );
};

export default AnnouncementDetail;

