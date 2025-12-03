import { doc, getDoc, setDoc } from 'firebase/firestore';
import { db } from '../config/firebase';
import { ApiResponse } from '../types';

/**
 * Firestore에서 프롬프트 조회
 */
export const getPrompt = async (): Promise<ApiResponse<{ content: string; metadata?: any }>> => {
  try {
    const promptRef = doc(db, 'settings', 'eap_review_prompt');
    const promptSnap = await getDoc(promptRef);

    if (!promptSnap.exists()) {
      return {
        success: false,
        error: '프롬프트가 설정되지 않았습니다.',
      };
    }

    const data = promptSnap.data();
    return {
      success: true,
      data: {
        content: data.content || '',
        metadata: {
          updated_at: data.updated_at,
          updated_by: data.updated_by,
        },
      },
    };
  } catch (error: any) {
    console.error('프롬프트 조회 실패:', error);
    return {
      success: false,
      error: error.message || '프롬프트를 불러오는데 실패했습니다.',
    };
  }
};

/**
 * Firestore에 프롬프트 저장
 */
export const savePrompt = async (content: string): Promise<ApiResponse<void>> => {
  try {
    const promptRef = doc(db, 'settings', 'eap_review_prompt');
    
    await setDoc(promptRef, {
      content,
      updated_at: new Date().toISOString(),
    }, { merge: true });

    return {
      success: true,
    };
  } catch (error: any) {
    console.error('프롬프트 저장 실패:', error);
    return {
      success: false,
      error: error.message || '프롬프트 저장에 실패했습니다.',
    };
  }
};

/**
 * 프롬프트 메타데이터 조회
 */
export const getPromptMetadata = async (): Promise<ApiResponse<{ updated_at?: string; updated_by?: string }>> => {
  try {
    const promptRef = doc(db, 'settings', 'eap_review_prompt');
    const promptSnap = await getDoc(promptRef);

    if (!promptSnap.exists()) {
      return {
        success: false,
        error: '프롬프트가 설정되지 않았습니다.',
      };
    }

    const data = promptSnap.data();
    return {
      success: true,
      data: {
        updated_at: data.updated_at,
        updated_by: data.updated_by,
      },
    };
  } catch (error: any) {
    console.error('프롬프트 메타데이터 조회 실패:', error);
    return {
      success: false,
      error: error.message || '프롬프트 메타데이터를 불러오는데 실패했습니다.',
    };
  }
};

