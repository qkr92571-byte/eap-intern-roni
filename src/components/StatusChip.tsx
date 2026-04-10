/**
 * 공고 상태를 표시하는 칩 컴포넌트
 */

import React from 'react';
import { Chip } from '@mui/material';
import { STATUS_LABELS, STATUS_COLORS } from '../utils/constants';
import { AnnouncementStatus } from '../types';

interface StatusChipProps {
  status: AnnouncementStatus;
  size?: 'small' | 'medium';
}

const StatusChip: React.FC<StatusChipProps> = ({ status, size = 'small' }) => {
  return (
    <Chip
      label={STATUS_LABELS[status] || status}
      color={STATUS_COLORS[status] || 'default'}
      size={size}
    />
  );
};

export default StatusChip;


