import axios from 'axios';
import { Announcement, ApiResponse } from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 공고 목록 조회
export const getAnnouncements = async (params?: {
  status?: string;
  limit?: number;
}): Promise<ApiResponse<Announcement[]>> => {
  const response = await api.get('/announcements', { params });
  return response.data;
};

// 공고 상세 조회
export const getAnnouncementById = async (
  id: string
): Promise<ApiResponse<Announcement>> => {
  const response = await api.get(`/announcements/${id}`);
  return response.data;
};

// 공고 수집 실행
export const scrapeAnnouncements = async (data: {
  keywords: string[];
}): Promise<ApiResponse<any[]>> => {
  const response = await api.post('/announcements/scrape', data);
  return response.data;
};

// 공고 필터링 및 검수
export const filterAnnouncements = async (data: {
  announcement_ids: string[];
  keywords?: string[];
}): Promise<ApiResponse<any[]>> => {
  const response = await api.post('/announcements/filter', data);
  return response.data;
};

// 공고 업데이트
export const updateAnnouncement = async (
  id: string,
  data: Partial<Announcement>
): Promise<ApiResponse<void>> => {
  const response = await api.put(`/announcements/${id}`, data);
  return response.data;
};

// 공고 삭제
export const deleteAnnouncement = async (
  id: string
): Promise<ApiResponse<void>> => {
  const response = await api.delete(`/announcements/${id}`);
  return response.data;
};

// 키워드 목록 조회
export const getKeywords = async (): Promise<ApiResponse<{ keywords: string[] }>> => {
  const response = await api.get('/keywords');
  return response.data;
};

// 키워드 추가
export const addKeyword = async (keyword: string): Promise<ApiResponse<{ keywords: string[] }>> => {
  const response = await api.post('/keywords', { keyword });
  return response.data;
};

// 키워드 삭제
export const deleteKeyword = async (keyword: string): Promise<ApiResponse<{ keywords: string[] }>> => {
  const response = await api.delete(`/keywords/${encodeURIComponent(keyword)}`);
  return response.data;
};

// 키워드 목록 업데이트
export const updateKeywords = async (keywords: string[]): Promise<ApiResponse<{ keywords: string[] }>> => {
  const response = await api.put('/keywords', { keywords });
  return response.data;
};

// 오늘 수집된 report 조회
export const getTodayReport = async (): Promise<ApiResponse<{ announcements: any[] }>> => {
  const response = await api.get('/reports/today');
  return response.data;
};

// Firestore에 업로드
export const uploadToFirestore = async (date?: string): Promise<ApiResponse<{ announcements: any[] }>> => {
  const response = await api.post('/reports/upload', date ? { date } : {});
  return response.data;
};

export default api;

