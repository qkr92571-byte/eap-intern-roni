import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Tabs,
  Tab,
  TextField,
  Button,
  Alert,
  CircularProgress,
} from '@mui/material';
import SaveIcon from '@mui/icons-material/Save';
import { getPrompt, savePrompt, getPromptMetadata } from '../services/promptApi';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`settings-tabpanel-${index}`}
      aria-labelledby={`settings-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );
}

const Settings: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [promptContent, setPromptContent] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [metadata, setMetadata] = useState<{ updated_at?: string; updated_by?: string } | null>(null);

  useEffect(() => {
    loadPrompt();
  }, []);

  const loadPrompt = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await getPrompt();
      if (response.success && response.data) {
        setPromptContent(response.data.content || '');
        setMetadata(response.data.metadata || null);
      } else {
        setError(response.error || '프롬프트를 불러오는데 실패했습니다.');
      }
    } catch (err: any) {
      setError(err.message || '프롬프트를 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!promptContent.trim()) {
      setError('프롬프트 내용을 입력해주세요.');
      return;
    }

    try {
      setSaving(true);
      setError(null);
      setSuccess(false);

      const response = await savePrompt(promptContent);
      if (response.success) {
        setSuccess(true);
        // 메타데이터 새로고침
        const metaResponse = await getPromptMetadata();
        if (metaResponse.success && metaResponse.data) {
          setMetadata(metaResponse.data);
        }
        setTimeout(() => setSuccess(false), 3000);
      } else {
        setError(response.error || '프롬프트 저장에 실패했습니다.');
      }
    } catch (err: any) {
      setError(err.message || '프롬프트 저장에 실패했습니다.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" component="h1" fontWeight="bold" mb={3}>
        설정
      </Typography>

      <Paper sx={{ p: 3 }}>
        <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)}>
          <Tab label="프롬프트" />
        </Tabs>

        <TabPanel value={tabValue} index={0}>
          <Box>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">EAP 검수 프롬프트</Typography>
              {metadata && (
                <Typography variant="caption" color="textSecondary">
                  최종 수정: {metadata.updated_at 
                    ? new Date(metadata.updated_at).toLocaleString('ko-KR')
                    : '-'}
                </Typography>
              )}
            </Box>

            {error && (
              <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
                {error}
              </Alert>
            )}

            {success && (
              <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(false)}>
                프롬프트가 성공적으로 저장되었습니다.
              </Alert>
            )}

            <TextField
              fullWidth
              multiline
              rows={20}
              value={promptContent}
              onChange={(e) => setPromptContent(e.target.value)}
              placeholder="프롬프트 내용을 입력하세요..."
              sx={{ mb: 2 }}
              variant="outlined"
            />

            <Box display="flex" justifyContent="flex-end" gap={2}>
              <Button
                variant="outlined"
                onClick={loadPrompt}
                disabled={saving}
              >
                취소
              </Button>
              <Button
                variant="contained"
                startIcon={<SaveIcon />}
                onClick={handleSave}
                disabled={saving || !promptContent.trim()}
              >
                {saving ? '저장 중...' : '저장'}
              </Button>
            </Box>

            <Box mt={3}>
              <Typography variant="body2" color="textSecondary">
                <strong>참고사항:</strong>
              </Typography>
              <Typography variant="body2" color="textSecondary" component="div" sx={{ mt: 1 }}>
                <ul style={{ margin: 0, paddingLeft: 20 }}>
                  <li>프롬프트는 AI 검수 시 사용됩니다.</li>
                  <li>프롬프트를 수정하면 다음 검수부터 새로운 프롬프트가 적용됩니다.</li>
                  <li>프롬프트는 Firestore에 저장되며, 파일 기반 프롬프트보다 우선순위가 높습니다.</li>
                </ul>
              </Typography>
            </Box>
          </Box>
        </TabPanel>
      </Paper>
    </Box>
  );
};

export default Settings;

