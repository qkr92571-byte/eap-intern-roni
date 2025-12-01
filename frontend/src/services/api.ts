import axios from 'axios';
import { collection, doc, getDoc, getDocs, limit as fsLimit, orderBy, query, where } from 'firebase/firestore';
import { db } from '../config/firebase';
import { Announcement, ApiResponse } from '../types';

// 호스팅 환경에서 백엔드 대신 Firestore를 직접 사용할지 여부
// - 개발 환경: 기본값 false (백엔드 API 사용)
// - 호스팅 빌드: REACT_APP_USE_FIRESTORE_DIRECT=true 로 설정
const USE_FIRESTORE_DIRECT = process.env.REACT_APP_USE_FIRESTORE_DIRECT === 'true';

// 현재 호스트 기반으로 API URL 동적 설정 (백엔드 모드일 때만 사용)
const getApiBaseUrl = () => {
  if (process.env.REACT_APP_API_URL) {
    return process.env.REACT_APP_API_URL;
  }
  
  // 현재 호스트가 localhost가 아니면 같은 호스트의 5001 포트 사용
  const hostname = window.location.hostname;
  if (hostname !== 'localhost' && hostname !== '127.0.0.1') {
    return `http://${hostname}:5001/api`;
  }
  
  return 'http://localhost:5001/api';
};

const API_BASE_URL = getApiBaseUrl();

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Firestore에서 공고 목록 조회 (호스팅 모드)
 */
const getAnnouncementsFromFirestore = async (params?: {
  status?: string;
  limit?: number;
}): Promise<ApiResponse<Announcement[]>> => {
  try {
    const { status, limit } = params || {};

    let q: any = collection(db, 'announcements');

    // 상태 필터
    if (status && status !== 'all') {
      q = query(q, where('status', '==', status));
    }

    // created_at 기준 내림차순 정렬
    q = query(q, orderBy('created_at', 'desc'), fsLimit(limit ?? 100));

    const snapshot = await getDocs(q);
    const announcements: Announcement[] = [];

    snapshot.forEach((docSnap) => {
      const data = docSnap.data() as any;
      announcements.push({
        id: docSnap.id,
        ...data,
      } as Announcement);
    });

    return {
      success: true,
      data: announcements,
      count: announcements.length,
    };
  } catch (error: any) {
    console.error('Firestore에서 공고 목록 조회 실패:', error);
    return {
      success: false,
      error: error.message || 'Firestore에서 공고 목록을 불러오는데 실패했습니다.',
    };
  }
};

/**
 * Firestore에서 단일 공고 조회 (호스팅 모드)
 */
const getAnnouncementByIdFromFirestore = async (
  id: string
): Promise<ApiResponse<Announcement>> => {
  try {
    const ref = doc(db, 'announcements', id);
    const snap = await getDoc(ref);

    if (!snap.exists()) {
      return {
        success: false,
        error: '공고를 찾을 수 없습니다.',
      };
    }

    const data = snap.data() as any;
    const announcement: Announcement = {
      id: snap.id,
      ...data,
    };

    return {
      success: true,
      data: announcement,
    };
  } catch (error: any) {
    console.error('Firestore에서 공고 상세 조회 실패:', error);
    return {
      success: false,
      error: error.message || 'Firestore에서 공고 상세 정보를 불러오는데 실패했습니다.',
    };
  }
};

// 공고 목록 조회
export const getAnnouncements = async (params?: {
  status?: string;
  limit?: number;
}): Promise<ApiResponse<Announcement[]>> => {
  // 호스팅 모드: Firestore 직접 조회
  if (USE_FIRESTORE_DIRECT) {
    return getAnnouncementsFromFirestore(params);
  }

  const response = await api.get('/announcements', { params });
  return response.data;
};

// 공고 상세 조회
export const getAnnouncementById = async (
  id: string
): Promise<ApiResponse<Announcement>> => {
  // 호스팅 모드: Firestore 직접 조회
  if (USE_FIRESTORE_DIRECT) {
    return getAnnouncementByIdFromFirestore(id);
  }

  const response = await api.get(`/announcements/${id}`);
  return response.data;
};

// 공고 수집 실행
export const scrapeAnnouncements = async (data: {
  keywords: string[];
}): Promise<ApiResponse<any[]>> => {
  // 호스팅 모드에서는 백엔드 기능 사용 불가
  if (USE_FIRESTORE_DIRECT) {
    return {
      success: false,
      error: '호스팅 환경에서는 공고 수집 기능을 사용할 수 없습니다. 로컬 개발 환경에서 백엔드 서버와 함께 실행해 주세요.',
    };
  }

  const response = await api.post('/announcements/scrape', data);
  return response.data;
};

// 공고 필터링 및 검수
export const filterAnnouncements = async (data: {
  announcement_ids: string[];
  keywords?: string[];
}): Promise<ApiResponse<any[]>> => {
  if (USE_FIRESTORE_DIRECT) {
    return {
      success: false,
      error: '호스팅 환경에서는 필터링/검수 기능을 사용할 수 없습니다. 로컬 개발 환경에서 백엔드 서버와 함께 실행해 주세요.',
    };
  }

  const response = await api.post('/announcements/filter', data);
  return response.data;
};

// 공고 업데이트
export const updateAnnouncement = async (
  id: string,
  data: Partial<Announcement>
): Promise<ApiResponse<void>> => {
  if (USE_FIRESTORE_DIRECT) {
    return {
      success: false,
      error: '호스팅 환경에서는 공고 업데이트 기능을 사용할 수 없습니다. 로컬 개발 환경에서 백엔드 서버와 함께 실행해 주세요.',
    };
  }

  const response = await api.put(`/announcements/${id}`, data);
  return response.data;
};

// 공고 삭제
export const deleteAnnouncement = async (
  id: string
): Promise<ApiResponse<void>> => {
  if (USE_FIRESTORE_DIRECT) {
    return {
      success: false,
      error: '호스팅 환경에서는 공고 삭제 기능을 사용할 수 없습니다. 로컬 개발 환경에서 백엔드 서버와 함께 실행해 주세요.',
    };
  }

  const response = await api.delete(`/announcements/${id}`);
  return response.data;
};

// 키워드 목록 조회
export const getKeywords = async (): Promise<ApiResponse<{ keywords: string[] }>> => {
  if (USE_FIRESTORE_DIRECT) {
    return {
      success: false,
      error: '호스팅 환경에서는 키워드 관리 기능을 사용할 수 없습니다. 로컬 개발 환경에서 백엔드 서버와 함께 실행해 주세요.',
    };
  }

  const response = await api.get('/keywords');
  return response.data;
};

// 키워드 추가
export const addKeyword = async (keyword: string): Promise<ApiResponse<{ keywords: string[] }>> => {
  if (USE_FIRESTORE_DIRECT) {
    return {
      success: false,
      error: '호스팅 환경에서는 키워드 관리 기능을 사용할 수 없습니다. 로컬 개발 환경에서 백엔드 서버와 함께 실행해 주세요.',
    };
  }

  const response = await api.post('/keywords', { keyword });
  return response.data;
};

// 키워드 삭제
export const deleteKeyword = async (keyword: string): Promise<ApiResponse<{ keywords: string[] }>> => {
  if (USE_FIRESTORE_DIRECT) {
    return {
      success: false,
      error: '호스팅 환경에서는 키워드 관리 기능을 사용할 수 없습니다. 로컬 개발 환경에서 백엔드 서버와 함께 실행해 주세요.',
    };
  }

  const response = await api.delete(`/keywords/${encodeURIComponent(keyword)}`);
  return response.data;
};

// 키워드 목록 업데이트
export const updateKeywords = async (keywords: string[]): Promise<ApiResponse<{ keywords: string[] }>> => {
  if (USE_FIRESTORE_DIRECT) {
    return {
      success: false,
      error: '호스팅 환경에서는 키워드 관리 기능을 사용할 수 없습니다. 로컬 개발 환경에서 백엔드 서버와 함께 실행해 주세요.',
    };
  }

  const response = await api.put('/keywords', { keywords });
  return response.data;
};

// 오늘 수집된 report 조회
export const getTodayReport = async (): Promise<ApiResponse<{ announcements: any[] }>> => {
  if (USE_FIRESTORE_DIRECT) {
    return {
      success: false,
      error: '호스팅 환경에서는 리포트 조회 기능을 사용할 수 없습니다. 로컬 개발 환경에서 백엔드 서버와 함께 실행해 주세요.',
    };
  }

  const response = await api.get('/reports/today');
  return response.data;
};

// Firestore에 업로드
export const uploadToFirestore = async (date?: string): Promise<ApiResponse<{ announcements: any[] }>> => {
  if (USE_FIRESTORE_DIRECT) {
    return {
      success: false,
      error: '호스팅 환경에서는 리포트 업로드 기능을 사용할 수 없습니다. 로컬 개발 환경에서 백엔드 서버와 함께 실행해 주세요.',
    };
  }

  const response = await api.post('/reports/upload', date ? { date } : {});
  return response.data;
};

export default api;

