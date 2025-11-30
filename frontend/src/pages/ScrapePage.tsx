import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  TextField,
  Button,
  Alert,
  CircularProgress,
  Chip,
  Stack,
  IconButton,
  InputAdornment,
} from '@mui/material';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import { scrapeAnnouncements, getKeywords, addKeyword, deleteKeyword, getTodayReport, uploadToFirestore } from '../services/api';

const ScrapePage: React.FC = () => {
  const [savedKeywords, setSavedKeywords] = useState<string[]>([]);
  const [newKeyword, setNewKeyword] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [keywordsLoading, setKeywordsLoading] = useState(true);
  const [result, setResult] = useState<{
    success: boolean;
    message?: string;
    error?: string;
    data?: any[];
  } | null>(null);
  const [reportData, setReportData] = useState<any[]>([]);
  const [showUploadConfirm, setShowUploadConfirm] = useState(false);

  useEffect(() => {
    loadKeywords();
    loadTodayReport();
  }, []);

  const loadTodayReport = async () => {
    try {
      const response = await getTodayReport();
      if (response.success && response.data) {
        setReportData(response.data.announcements || []);
      }
    } catch (error: any) {
      console.error('Report 로드 실패:', error);
    }
  };

  const loadKeywords = async () => {
    try {
      setKeywordsLoading(true);
      const response = await getKeywords();
      if (response.success && response.data) {
        // API 응답 형식: { keywords: string[] }
        const keywords = response.data.keywords || (Array.isArray(response.data) ? response.data : []);
        setSavedKeywords(keywords);
      }
    } catch (error: any) {
      console.error('키워드 로드 실패:', error);
    } finally {
      setKeywordsLoading(false);
    }
  };

  const handleAddKeyword = async () => {
    if (!newKeyword.trim()) {
      return;
    }

    try {
      const response = await addKeyword(newKeyword.trim());
      if (response.success && response.data) {
        setSavedKeywords(response.data.keywords || []);
        setNewKeyword('');
      }
    } catch (error: any) {
      console.error('키워드 추가 실패:', error);
    }
  };

  const handleDeleteKeyword = async (keyword: string) => {
    try {
      const response = await deleteKeyword(keyword);
      if (response.success && response.data) {
        setSavedKeywords(response.data.keywords || []);
      }
    } catch (error: any) {
      console.error('키워드 삭제 실패:', error);
    }
  };

  const handleScrape = async () => {
    try {
      setLoading(true);
      setResult(null);

      // 저장된 키워드 사용 (없으면 빈 배열)
      const keywordList = savedKeywords.length > 0 ? savedKeywords : [];

      const response = await scrapeAnnouncements({ keywords: keywordList });

      setResult({
        success: response.success,
        message: response.message,
        data: response.data,
      });
      
      // 수집 완료 후 report 다시 로드
      if (response.success) {
        await loadTodayReport();
      }
    } catch (error: any) {
      setResult({
        success: false,
        error: error.message || '수집 중 오류가 발생했습니다.',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleUploadConfirm = async () => {
    try {
      setUploading(true);
      const response = await uploadToFirestore();
      
      if (response.success) {
        setResult({
          success: true,
          message: response.message || 'Firestore에 업로드되었습니다.',
        });
        setShowUploadConfirm(false);
        // 업로드 후 report 다시 로드
        await loadTodayReport();
      } else {
        setResult({
          success: false,
          error: response.error || '업로드 중 오류가 발생했습니다.',
        });
      }
    } catch (error: any) {
      setResult({
        success: false,
        error: error.message || '업로드 중 오류가 발생했습니다.',
      });
    } finally {
      setUploading(false);
    }
  };

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        공고 수집
      </Typography>

      {/* 키워드 관리 섹션 */}
      <Paper sx={{ p: 3, mt: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          검색 키워드 관리
        </Typography>

        <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
          수집에 사용할 키워드를 추가하거나 삭제할 수 있습니다.
        </Typography>

        {/* 키워드 추가 */}
        <Box sx={{ mb: 2 }}>
          <TextField
            fullWidth
            size="small"
            label="새 키워드 추가"
            placeholder="키워드를 입력하세요"
            value={newKeyword}
            onChange={(e) => setNewKeyword(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                handleAddKeyword();
              }
            }}
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    onClick={handleAddKeyword}
                    disabled={!newKeyword.trim()}
                    color="primary"
                  >
                    <AddIcon />
                  </IconButton>
                </InputAdornment>
              ),
            }}
            sx={{ mb: 2 }}
          />
        </Box>

        {/* 저장된 키워드 목록 */}
        {keywordsLoading ? (
          <Box display="flex" justifyContent="center" p={2}>
            <CircularProgress size={24} />
          </Box>
        ) : (
          <Box>
            {savedKeywords.length > 0 ? (
              <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                {savedKeywords.map((keyword) => (
                  <Chip
                    key={keyword}
                    label={keyword}
                    onDelete={() => handleDeleteKeyword(keyword)}
                    deleteIcon={<DeleteIcon />}
                    color="primary"
                    variant="outlined"
                    sx={{ mb: 1 }}
                  />
                ))}
              </Stack>
            ) : (
              <Typography variant="body2" color="textSecondary">
                저장된 키워드가 없습니다. 키워드를 추가해주세요.
              </Typography>
            )}
          </Box>
        )}
      </Paper>

      {/* 수집 실행 섹션 */}
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          공고 수집 실행
        </Typography>

        <Typography variant="body2" color="textSecondary" sx={{ mb: 3 }}>
          저장된 키워드로 나라장터에서 최신 공고를 수집합니다.
          {savedKeywords.length > 0 ? (
            <> 현재 {savedKeywords.length}개의 키워드가 설정되어 있습니다.</>
          ) : (
            <> 키워드가 없으면 기본 키워드로 검색합니다.</>
          )}
        </Typography>

        <Box sx={{ mb: 2, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <Button
            variant="contained"
            color="primary"
            size="large"
            startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <PlayArrowIcon />}
            onClick={handleScrape}
            disabled={loading || keywordsLoading}
            sx={{ minWidth: 200 }}
          >
            {loading ? '수집 중...' : '수집 시작'}
          </Button>
          
          {reportData.length > 0 && (
            <Button
              variant="contained"
              color="success"
              size="large"
              startIcon={uploading ? <CircularProgress size={20} color="inherit" /> : <CloudUploadIcon />}
              onClick={() => setShowUploadConfirm(true)}
              disabled={uploading || loading}
              sx={{ minWidth: 200 }}
            >
              {uploading ? '업로드 중...' : `Firestore 업로드 (${reportData.length}개)`}
            </Button>
          )}
        </Box>
        
        {reportData.length > 0 && !showUploadConfirm && (
          <Alert severity="info" sx={{ mb: 2 }}>
            오늘 수집된 공고: {reportData.length}개 (파일로 저장됨)
            {' → '}Firestore에 업로드하려면 버튼을 클릭하세요.
          </Alert>
        )}
        
        {showUploadConfirm && (
          <Alert 
            severity="warning" 
            sx={{ mb: 2 }}
            action={
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button
                  color="inherit"
                  size="small"
                  onClick={() => setShowUploadConfirm(false)}
                >
                  취소
                </Button>
                <Button
                  color="inherit"
                  size="small"
                  onClick={handleUploadConfirm}
                  disabled={uploading}
                >
                  확인
                </Button>
              </Box>
            }
          >
            {reportData.length}개의 공고를 Firestore에 업로드하시겠습니까?
          </Alert>
        )}

        {result && (
          <Box sx={{ mt: 3 }}>
            {result.success ? (
              <Alert severity="success" sx={{ mb: 2 }}>
                {result.message || '수집이 완료되었습니다.'}
              </Alert>
            ) : (
              <Alert severity="error" sx={{ mb: 2 }}>
                {result.error || '오류가 발생했습니다.'}
              </Alert>
            )}

            {result.data && result.data.length > 0 && (
              <Box>
                <Typography variant="subtitle1" gutterBottom>
                  수집된 공고 ({result.data.length}개):
                </Typography>
                <Stack direction="row" spacing={1} flexWrap="wrap">
                  {result.data.slice(0, 10).map((item: any, index: number) => (
                    <Chip
                      key={index}
                      label={item.title || `공고 ${index + 1}`}
                      size="small"
                    />
                  ))}
                  {result.data.length > 10 && (
                    <Chip label={`+${result.data.length - 10}개 더...`} size="small" />
                  )}
                </Stack>
              </Box>
            )}
          </Box>
        )}
      </Paper>
    </Box>
  );
};

export default ScrapePage;

