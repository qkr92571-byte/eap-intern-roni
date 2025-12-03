import { collection, doc, getDoc, getDocs, limit as fsLimit, query } from 'firebase/firestore';
import { db } from '../config/firebase';
import { Announcement, ApiResponse } from '../types';

/**
 * Firestore에서 공고 목록 조회
 */
const getAnnouncementsFromFirestore = async (params?: {
  status?: string;
  limit?: number;
}): Promise<ApiResponse<Announcement[]>> => {
  try {
    const { limit } = params || {};

    const q = collection(db, 'announcements');

    // 정렬 없이 먼저 조회 (인덱스 문제 방지)
    const snapshot = await getDocs(query(q, fsLimit(limit ?? 200)));
    
    const announcements: Announcement[] = [];

    snapshot.forEach((docSnap) => {
      const data = docSnap.data() as any;
      announcements.push({
        id: docSnap.id,
        ...data,
      } as Announcement);
    });

    // 클라이언트 측에서 정렬 (created_at 또는 publish_date 기준)
    announcements.sort((a, b) => {
      // publish_date 우선, 없으면 created_at 사용
      const dateA = a.publish_date 
        ? new Date(a.publish_date.replace(/\//g, '-')).getTime()
        : a.created_at 
        ? new Date(a.created_at).getTime() 
        : 0;
      const dateB = b.publish_date 
        ? new Date(b.publish_date.replace(/\//g, '-')).getTime()
        : b.created_at 
        ? new Date(b.created_at).getTime() 
        : 0;
      return dateB - dateA; // 내림차순 (최신순)
    });

    // limit 적용
    if (limit && announcements.length > limit) {
      announcements.splice(limit);
    }

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
 * Firestore에서 단일 공고 조회
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
  return getAnnouncementsFromFirestore(params);
};

// 공고 상세 조회
export const getAnnouncementById = async (
  id: string
): Promise<ApiResponse<Announcement>> => {
  return getAnnouncementByIdFromFirestore(id);
};

// 백엔드 전용 기능들 (프론트엔드에서 사용 불가)
// 공고 수집, 필터링, 키워드 관리, 리포트 조회/업로드 등은 백엔드에서만 가능

/**
 * Firestore에서 경쟁사 동향 데이터 조회
 */
const getCompetitorAwardsFromFirestore = async (params?: {
  limit?: number;
}): Promise<ApiResponse<any[]>> => {
  try {
    const { limit } = params || {};

    const q = collection(db, 'competitor_awards');

    // 정렬 없이 먼저 조회 (인덱스 문제 방지)
    const snapshot = await getDocs(query(q, fsLimit(limit ?? 200)));
    
    const awards: any[] = [];

    snapshot.forEach((docSnap) => {
      const data = docSnap.data() as Record<string, any>;
      if (data) {
        awards.push({
          id: docSnap.id,
          ...data,
        });
      }
    });

    // 클라이언트 측에서 정렬 (created_at 기준)
    awards.sort((a, b) => {
      const dateA = a.created_at ? new Date(a.created_at).getTime() : 0;
      const dateB = b.created_at ? new Date(b.created_at).getTime() : 0;
      return dateB - dateA;
    });

    // limit 적용
    if (limit && awards.length > limit) {
      awards.splice(limit);
    }

    return {
      success: true,
      data: awards,
      count: awards.length,
    };
  } catch (error: any) {
    console.error('[경쟁사 동향] Firestore 조회 실패:', error);
    console.error('[경쟁사 동향] 에러 상세:', error.code, error.message, error.stack);
    
    // 보안 규칙 에러인 경우 명확한 메시지 제공
    if (error.code === 'permission-denied' || error.message?.includes('permission')) {
      return {
        success: false,
        error: 'Firestore 보안 규칙: competitor_awards 컬렉션에 대한 읽기 권한이 없습니다. Firebase 콘솔에서 보안 규칙을 확인해주세요.',
      };
    }
    
    return {
      success: false,
      error: error.message || 'Firestore에서 경쟁사 동향을 불러오는데 실패했습니다.',
    };
  }
};

// 경쟁사 동향 조회
export const getCompetitorAwards = async (params?: {
  limit?: number;
}): Promise<ApiResponse<any[]>> => {
  return getCompetitorAwardsFromFirestore(params);
};

