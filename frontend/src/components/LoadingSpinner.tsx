/**
 * 로딩 스피너 컴포넌트
 */

import React from 'react';
import { Box, CircularProgress } from '@mui/material';

interface LoadingSpinnerProps {
  minHeight?: number | string;
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ minHeight = 400 }) => {
  return (
    <Box 
      display="flex" 
      justifyContent="center" 
      alignItems="center" 
      minHeight={minHeight}
    >
      <CircularProgress />
    </Box>
  );
};

export default LoadingSpinner;


