/**
 * 공통 타입 정의
 */

export interface Announcement {
  id: string;
  // 필수 필드
  title: string;
  announcement_number: string;
  agency: string;
  created_at: string;
  
  // 선택 필드
  budget_amount?: number;  // 예산금액 (원 단위 숫자)
  estimated_price?: number;  // 추정가격 (원 단위 숫자)
  business_type?: string;  // 사업구분
  announcement_status?: string;  // 공고상태 (나라장터 원본 상태)
  deadline?: string;  // 마감일
  publish_date?: string;  // 게시일 (YYYY/MM/DD 형식)
  url?: string;  // 원본 링크
  content?: string;  // 공고 내용
  category?: string;  // 카테고리
  
  // 시스템 필드
  status: AnnouncementStatus;  // pending, approved, rejected
  filtered?: boolean;
  reviewed?: boolean;
  review_result?: string;  // 검수 결과
  source?: string;  // 출처 (기본값: '나라장터')
  
  // 표시 상태 필드
  display_status?: number;  // 20: 노출, 40: 삭제됨 (숨김)
  
  // 서비스 항목 필드
  service_items?: ServiceItem[];  // 요구 서비스 항목 리스트
  service_items_extracted_at?: string;  // 서비스 항목 추출 일시
}

export interface ServiceItem {
  구분: string;  // 서비스 항목명
  설명: string;  // 서비스 항목 설명
}

export type AnnouncementStatus = 'pending' | 'approved' | 'rejected';

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
  count?: number;
}

export interface Stats {
  total: number;
  approved: number;
  pending: number;
  rejected: number;
}


