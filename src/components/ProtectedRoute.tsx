/**
 * 인증 및 승인 여부에 따라 라우트를 보호하는 컴포넌트
 * - 미로그인 → /login 리다이렉트
 * - 로그인 + 미승인 → 승인 대기 안내 화면
 * - 로그인 + 승인 완료 → 정상 렌더링
 */

import React from 'react';
import { Navigate } from 'react-router-dom';
import { Box, Typography, CircularProgress, Paper } from '@mui/material';
import HourglassEmptyIcon from '@mui/icons-material/HourglassEmpty';
import { useAuth } from '../contexts/AuthContext';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { currentUser, userProfile, loading } = useAuth();

  // Auth 초기화 중
  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh">
        <CircularProgress />
      </Box>
    );
  }

  // 미로그인 → 로그인 페이지로
  if (!currentUser) {
    return <Navigate to="/login" replace />;
  }

  // 승인 대기 중
  if (!userProfile?.approved) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight="100vh"
        bgcolor="grey.100"
      >
        <Paper sx={{ p: 6, textAlign: 'center', maxWidth: 400 }}>
          <HourglassEmptyIcon sx={{ fontSize: 64, color: 'warning.main', mb: 2 }} />
          <Typography variant="h5" fontWeight="bold" mb={1}>
            승인 대기 중
          </Typography>
          <Typography color="text.secondary" mb={3}>
            관리자의 승인 후 서비스를 이용하실 수 있습니다.
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {currentUser.email}
          </Typography>
          <Box mt={3}>
            <Typography
              variant="body2"
              color="primary"
              sx={{ cursor: 'pointer', textDecoration: 'underline' }}
              onClick={() => {
                import('../contexts/AuthContext').then(({ useAuth: _ }) => {});
                // logout은 Layout에서 처리하므로 여기선 auth.signOut 직접 호출
                import('firebase/auth').then(({ getAuth, signOut }) => {
                  signOut(getAuth());
                });
              }}
            >
              다른 계정으로 로그인
            </Typography>
          </Box>
        </Paper>
      </Box>
    );
  }

  return <>{children}</>;
};

export default ProtectedRoute;
