import { collection, doc, getDoc, getDocs, limit as fsLimit, query, setDoc, updateDoc, where } from 'firebase/firestore';
import { db } from '../config/firebase';
import { Announcement, ApiResponse, UserProfile } from '../types';

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

    // display_status=20(노출)인 것만 서버에서 필터링 (삭제된 공고 제외)
    // 정렬은 인덱스 문제 방지를 위해 클라이언트에서 수행
    const snapshot = await getDocs(
      limit
        ? query(q, where('display_status', '==', 20), fsLimit(limit))
        : query(q, where('display_status', '==', 20))
    );

    const announcements: Announcement[] = [];

    snapshot.forEach((docSnap) => {
      const data = docSnap.data() as any;
      announcements.push({
        id: docSnap.id,
        ...data,
      } as Announcement);
    });

    // 클라이언트 측에서 정렬 (created_at 기준, 수집일순)
    announcements.sort((a, b) => {
      // created_at 우선, 없으면 publish_date 사용
      const dateA = a.created_at 
        ? new Date(a.created_at).getTime()
        : a.publish_date 
        ? new Date(a.publish_date.replace(/\//g, '-')).getTime()
        : 0;
      const dateB = b.created_at 
        ? new Date(b.created_at).getTime()
        : b.publish_date 
        ? new Date(b.publish_date.replace(/\//g, '-')).getTime()
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

/**
 * 공고 상태 업데이트
 */
export const updateAnnouncementStatus = async (
  id: string,
  status: 'approved' | 'rejected' | 'pending'
): Promise<ApiResponse<void>> => {
  try {
    const { updateDoc, doc } = await import('firebase/firestore');
    const { db } = await import('../config/firebase');
    
    const ref = doc(db, 'announcements', id);
    await updateDoc(ref, {
      status,
      reviewed: true,
    });

    return {
      success: true,
      message: '공고 상태가 업데이트되었습니다.',
    };
  } catch (error: any) {
    console.error('공고 상태 업데이트 실패:', error);
    return {
      success: false,
      error: error.message || '공고 상태를 업데이트하는데 실패했습니다.',
    };
  }
};

/**
 * 공고 삭제 (display_status를 40으로 변경하여 숨김 처리)
 */
export const deleteAnnouncement = async (
  id: string
): Promise<ApiResponse<void>> => {
  try {
    const { updateDoc, doc } = await import('firebase/firestore');
    const { db } = await import('../config/firebase');
    
    const ref = doc(db, 'announcements', id);
    await updateDoc(ref, {
      display_status: 40, // 삭제됨 (숨김)
    });

    return {
      success: true,
      message: '공고가 삭제되었습니다. (숨김 처리)',
    };
  } catch (error: any) {
    console.error('공고 삭제 실패:', error);
    return {
      success: false,
      error: error.message || '공고를 삭제하는데 실패했습니다.',
    };
  }
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

/**
 * 회원가입 시 Firestore users 컬렉션에 사용자 프로필 생성
 * - 기본값: role='default', approved=false
 */
export const createUserProfile = async (
  uid: string,
  email: string
): Promise<ApiResponse<void>> => {
  try {
    const ref = doc(db, 'users', uid);
    await setDoc(ref, {
      uid,
      email,
      role: 'default',
      approved: false,
      created_at: new Date().toISOString(),
    });
    return { success: true };
  } catch (error: any) {
    console.error('사용자 프로필 생성 실패:', error);
    return { success: false, error: error.message };
  }
};

/**
 * Firestore에서 사용자 프로필 조회
 */
export const getUserProfile = async (uid: string): Promise<ApiResponse<UserProfile>> => {
  try {
    const ref = doc(db, 'users', uid);
    const snap = await getDoc(ref);
    if (!snap.exists()) {
      return { success: false, error: '사용자 프로필을 찾을 수 없습니다.' };
    }
    return { success: true, data: snap.data() as UserProfile };
  } catch (error: any) {
    console.error('사용자 프로필 조회 실패:', error);
    return { success: false, error: error.message };
  }
};

/**
 * 전체 사용자 목록 조회 (admin 전용)
 */
export const getAllUsers = async (): Promise<ApiResponse<UserProfile[]>> => {
  try {
    const snapshot = await getDocs(collection(db, 'users'));
    const users: UserProfile[] = [];
    snapshot.forEach((docSnap) => {
      users.push(docSnap.data() as UserProfile);
    });
    // 가입일 기준 최신순 정렬
    users.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
    return { success: true, data: users };
  } catch (error: any) {
    console.error('사용자 목록 조회 실패:', error);
    return { success: false, error: error.message };
  }
};

/**
 * 사용자 승인 처리 (admin 전용)
 */
export const approveUser = async (uid: string): Promise<ApiResponse<void>> => {
  try {
    const ref = doc(db, 'users', uid);
    await updateDoc(ref, { approved: true });
    return { success: true };
  } catch (error: any) {
    console.error('사용자 승인 실패:', error);
    return { success: false, error: error.message };
  }
};

/**
 * 사용자 역할 변경 (admin 전용)
 */
export const updateUserRole = async (
  uid: string,
  role: 'admin' | 'default'
): Promise<ApiResponse<void>> => {
  try {
    const ref = doc(db, 'users', uid);
    await updateDoc(ref, { role });
    return { success: true };
  } catch (error: any) {
    console.error('사용자 역할 변경 실패:', error);
    return { success: false, error: error.message };
  }
};

