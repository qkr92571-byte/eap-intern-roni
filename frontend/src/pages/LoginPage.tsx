/**
 * 로그인 / 회원가입 페이지
 * - 이메일/비밀번호 방식
 * - 같은 페이지에서 로그인/회원가입 토글
 */

import React, { useState } from 'react';
import { Navigate } from 'react-router-dom';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Alert,
  CircularProgress,
  Divider,
} from '@mui/material';
import { useAuth } from '../contexts/AuthContext';

const LoginPage: React.FC = () => {
  const { currentUser, userProfile, loading, login, signup } = useAuth();
  const [isSignup, setIsSignup] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [signupSuccess, setSignupSuccess] = useState(false);

  // 이미 로그인 + 승인된 경우 홈으로 이동
  if (!loading && currentUser && userProfile?.approved) {
    return <Navigate to="/" replace />;
  }

  const translateFirebaseError = (code: string): string => {
    switch (code) {
      case 'auth/user-not-found':
      case 'auth/wrong-password':
      case 'auth/invalid-credential':
        return '이메일 또는 비밀번호가 올바르지 않습니다.';
      case 'auth/email-already-in-use':
        return '이미 사용 중인 이메일입니다.';
      case 'auth/weak-password':
        return '비밀번호는 6자 이상이어야 합니다.';
      case 'auth/invalid-email':
        return '유효하지 않은 이메일 형식입니다.';
      case 'auth/too-many-requests':
        return '로그인 시도가 너무 많습니다. 잠시 후 다시 시도해주세요.';
      default:
        return '오류가 발생했습니다. 다시 시도해주세요.';
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (isSignup && password !== confirmPassword) {
      setError('비밀번호가 일치하지 않습니다.');
      return;
    }

    try {
      setSubmitting(true);
      if (isSignup) {
        await signup(email, password);
        setSignupSuccess(true);
      } else {
        await login(email, password);
      }
    } catch (err: any) {
      setError(translateFirebaseError(err.code));
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box
      display="flex"
      justifyContent="center"
      alignItems="center"
      minHeight="100vh"
      bgcolor="grey.100"
    >
      <Paper sx={{ p: 5, width: '100%', maxWidth: 420 }}>
        {/* 로고 */}
        <Box textAlign="center" mb={3}>
          <Box
            component="img"
            src="/logo.png"
            alt="인턴 로니"
            sx={{ height: 64, mb: 1 }}
          />
          <Typography variant="h5" fontWeight="bold">
            인턴 로니
          </Typography>
          <Typography variant="body2" color="text.secondary">
            나라장터 사업 공고 수집 시스템
          </Typography>
        </Box>

        {/* 회원가입 성공 메시지 */}
        {signupSuccess && (
          <Alert severity="success" sx={{ mb: 2 }}>
            회원가입이 완료되었습니다. 관리자 승인 후 서비스를 이용하실 수 있습니다.
          </Alert>
        )}

        {/* 에러 메시지 */}
        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        <form onSubmit={handleSubmit}>
          <TextField
            fullWidth
            label="이메일"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            sx={{ mb: 2 }}
            autoComplete="email"
          />
          <TextField
            fullWidth
            label="비밀번호"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            sx={{ mb: isSignup ? 2 : 3 }}
            autoComplete={isSignup ? 'new-password' : 'current-password'}
          />
          {isSignup && (
            <TextField
              fullWidth
              label="비밀번호 확인"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              sx={{ mb: 3 }}
              autoComplete="new-password"
            />
          )}

          <Button
            fullWidth
            variant="contained"
            type="submit"
            size="large"
            disabled={submitting}
          >
            {submitting ? (
              <CircularProgress size={24} color="inherit" />
            ) : isSignup ? (
              '회원가입'
            ) : (
              '로그인'
            )}
          </Button>
        </form>

        <Divider sx={{ my: 2 }} />

        <Box textAlign="center">
          <Typography variant="body2" color="text.secondary">
            {isSignup ? '이미 계정이 있으신가요?' : '계정이 없으신가요?'}
          </Typography>
          <Button
            variant="text"
            size="small"
            onClick={() => {
              setIsSignup(!isSignup);
              setError(null);
              setSignupSuccess(false);
            }}
          >
            {isSignup ? '로그인' : '회원가입'}
          </Button>
        </Box>
      </Paper>
    </Box>
  );
};

export default LoginPage;
