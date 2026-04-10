/**
 * 상수 정의
 */

export const ANNOUNCEMENT_STATUS = {
  APPROVED: 'approved',
  REJECTED: 'rejected',
} as const;

export const STATUS_LABELS: Record<string, string> = {
  [ANNOUNCEMENT_STATUS.APPROVED]: '승인됨',
  [ANNOUNCEMENT_STATUS.REJECTED]: '거부됨',
};

export const STATUS_COLORS: Record<string, 'success' | 'error' | 'default'> = {
  [ANNOUNCEMENT_STATUS.APPROVED]: 'success',
  [ANNOUNCEMENT_STATUS.REJECTED]: 'error',
};

export const DEFAULT_PAGE_SIZE = 100;
export const MAX_PAGE_SIZE = 1000;


