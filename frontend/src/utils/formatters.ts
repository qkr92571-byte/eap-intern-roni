/**
 * 포맷팅 유틸리티 함수
 */

/**
 * 예산 금액을 읽기 쉬운 형식으로 변환
 */
export const formatBudget = (amount?: number): string => {
  if (!amount) return '-';
  
  if (amount >= 1000000000) {
    return `${(amount / 1000000000).toFixed(1)}억원`;
  } else if (amount >= 1000000) {
    return `${(amount / 1000000).toFixed(1)}백만원`;
  } else {
    return `${amount.toLocaleString('ko-KR')}원`;
  }
};

/**
 * 날짜를 한국어 형식으로 변환
 */
export const formatDate = (dateString?: string): string => {
  if (!dateString) return '-';
  
  try {
    return new Date(dateString).toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  } catch {
    return dateString;
  }
};

/**
 * 날짜를 간단한 형식으로 변환 (YYYY-MM-DD)
 */
export const formatDateShort = (dateString?: string): string => {
  if (!dateString) return '-';
  
  try {
    return new Date(dateString).toLocaleDateString('ko-KR');
  } catch {
    return dateString;
  }
};

/**
 * 숫자를 천 단위 구분자로 포맷팅
 */
export const formatNumber = (num?: number): string => {
  if (num === undefined || num === null) return '-';
  return num.toLocaleString('ko-KR');
};

/**
 * 공고번호를 기반으로 나라장터 상세 페이지 URL 생성
 * @param announcementNumber 공고번호 (예: "R25BK01187770-000")
 * @returns 나라장터 상세 페이지 URL
 */
export const getNaraJangteoUrl = (announcementNumber?: string): string | null => {
  if (!announcementNumber) return null;
  
  // 공고번호 형식: "R25BK01187770-000" 또는 "2026NIT001013039-01"
  const parts = announcementNumber.split('-');
  const bidPbancNo = parts[0]; // 하이픈 앞 부분
  const rawOrd = parts[1] || '000';
  const bidPbancOrd = rawOrd.padStart(3, '0'); // 항상 3자리로 패딩 (예: '01' → '001')
  
  return `https://www.g2b.go.kr/link/PNPE027_01/single/?bidPbancNo=${bidPbancNo}&bidPbancOrd=${bidPbancOrd}`;
};


