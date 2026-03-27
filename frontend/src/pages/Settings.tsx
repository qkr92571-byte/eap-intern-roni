import React, { useState, useEffect, useCallback } from 'react';
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
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  Chip,
  Select,
  MenuItem,
} from '@mui/material';
import SaveIcon from '@mui/icons-material/Save';
import CheckIcon from '@mui/icons-material/Check';
import { getPrompt, savePrompt, getPromptMetadata } from '../services/promptApi';
import { getAllUsers, approveUser, updateUserRole } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { UserProfile } from '../types';

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
  const { userProfile } = useAuth();
  const isAdmin = userProfile?.role === 'admin';

  const [tabValue, setTabValue] = useState(0);

  // 프롬프트 탭 상태
  const [promptContent, setPromptContent] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [metadata, setMetadata] = useState<{ updated_at?: string; updated_by?: string } | null>(null);

  // 사용자 관리 탭 상태
  const [users, setUsers] = useState<UserProfile[]>([]);
  const [usersLoading, setUsersLoading] = useState(false);
  const [usersError, setUsersError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  useEffect(() => {
    loadPrompt();
  }, []);

  const loadUsers = useCallback(async () => {
    setUsersLoading(true);
    setUsersError(null);
    const response = await getAllUsers();
    if (response.success && response.data) {
      setUsers(response.data);
    } else {
      setUsersError(response.error || '사용자 목록을 불러오는데 실패했습니다.');
    }
    setUsersLoading(false);
  }, []);

  useEffect(() => {
    if (isAdmin && tabValue === 1) {
      loadUsers();
    }
  }, [isAdmin, tabValue, loadUsers]);

  const handleApprove = async (uid: string) => {
    setActionLoading(uid);
    const response = await approveUser(uid);
    if (response.success) {
      setUsers((prev) => prev.map((u) => u.uid === uid ? { ...u, approved: true } : u));
    } else {
      setUsersError(response.error || '승인에 실패했습니다.');
    }
    setActionLoading(null);
  };

  const handleRoleChange = async (uid: string, role: 'admin' | 'default') => {
    setActionLoading(uid + '_role');
    const response = await updateUserRole(uid, role);
    if (response.success) {
      setUsers((prev) => prev.map((u) => u.uid === uid ? { ...u, role } : u));
    } else {
      setUsersError(response.error || '역할 변경에 실패했습니다.');
    }
    setActionLoading(null);
  };

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
          {isAdmin && <Tab label="사용자 관리" />}
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

        {/* 사용자 관리 탭 (admin 전용) */}
        {isAdmin && (
          <TabPanel value={tabValue} index={1}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">사용자 관리</Typography>
              <Button variant="outlined" size="small" onClick={loadUsers} disabled={usersLoading}>
                새로고침
              </Button>
            </Box>

            {usersError && (
              <Alert severity="error" sx={{ mb: 2 }} onClose={() => setUsersError(null)}>
                {usersError}
              </Alert>
            )}

            {usersLoading ? (
              <Box display="flex" justifyContent="center" py={4}>
                <CircularProgress />
              </Box>
            ) : (
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>이메일</TableCell>
                    <TableCell>가입일</TableCell>
                    <TableCell>승인 상태</TableCell>
                    <TableCell>권한</TableCell>
                    <TableCell>액션</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {users.map((user) => (
                    <TableRow key={user.uid}>
                      <TableCell>{user.email}</TableCell>
                      <TableCell>
                        {new Date(user.created_at).toLocaleDateString('ko-KR')}
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={user.approved ? '승인' : '대기'}
                          color={user.approved ? 'success' : 'warning'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Select
                          value={user.role}
                          size="small"
                          disabled={actionLoading === user.uid + '_role'}
                          onChange={(e) =>
                            handleRoleChange(user.uid, e.target.value as 'admin' | 'default')
                          }
                          sx={{ minWidth: 90, fontSize: '0.875rem' }}
                        >
                          <MenuItem value="default">default</MenuItem>
                          <MenuItem value="admin">admin</MenuItem>
                        </Select>
                      </TableCell>
                      <TableCell>
                        {!user.approved && (
                          <Button
                            variant="contained"
                            size="small"
                            color="success"
                            startIcon={<CheckIcon />}
                            disabled={actionLoading === user.uid}
                            onClick={() => handleApprove(user.uid)}
                          >
                            승인
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                  {users.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={5} align="center" sx={{ py: 4, color: 'text.secondary' }}>
                        등록된 사용자가 없습니다.
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            )}
          </TabPanel>
        )}
      </Paper>
    </Box>
  );
};

export default Settings;

