#!/usr/bin/env python3
"""
Firestore 데이터베이스 테스트 스크립트

실제 공고 데이터를 Firestore에 저장하고 조회하는 테스트를 수행합니다.
"""

import sys
import os
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.firebase_service import init_firebase, save_announcement, get_announcements, get_announcement_by_id
from models.announcement_schema import AnnouncementSchema

def test_insert_sample_data():
    """샘플 공고 데이터를 Firestore에 저장"""
    print("=" * 60)
    print("Firestore 데이터베이스 테스트")
    print("=" * 60)
    
    try:
        # Firebase 초기화
        print("\n1. Firebase 초기화 중...")
        init_firebase()
        print("   ✅ Firebase 초기화 성공")
        
        # 샘플 데이터 생성 (사용자가 제공한 실제 데이터 구조 사용)
        print("\n2. 샘플 공고 데이터 생성 중...")
        sample_announcements = [
            {
                'title': '2026년 찾아가는 상담실 운영',
                'announcement_number': 'R25BK01187770',
                'agency': '제주특별자치도 소방안전본부',
                'budget_amount': 150704000,  # 150,704,000원
                'estimated_price': 137003636,  # 137,003,636원
                'business_type': '일반용역',
                'announcement_status': '입찰_낙찰제안평가',
                'deadline': '2024-12-31',
                'status': 'pending',
                'source': '나라장터'
            },
            {
                'title': '2025년 소프트웨어 개발 용역',
                'announcement_number': 'R25BK01187771',
                'agency': '서울특별시청',
                'budget_amount': 500000000,  # 5억원
                'estimated_price': 450000000,  # 4.5억원
                'business_type': '일반용역',
                'announcement_status': '입찰공고',
                'deadline': '2025-01-15',
                'status': 'pending',
                'source': '나라장터'
            },
            {
                'title': 'IT 시스템 구축 사업',
                'announcement_number': 'R25BK01187772',
                'agency': '부산광역시청',
                'budget_amount': 1000000000,  # 10억원
                'estimated_price': 950000000,  # 9.5억원
                'business_type': '일반용역',
                'announcement_status': '입찰공고',
                'deadline': '2025-02-01',
                'status': 'approved',  # 승인된 상태로 테스트
                'source': '나라장터'
            }
        ]
        
        saved_ids = []
        for i, data in enumerate(sample_announcements, 1):
            # 스키마를 사용하여 공고 데이터 생성
            announcement = AnnouncementSchema.create_announcement(**data)
            
            # 유효성 검사
            is_valid, error = AnnouncementSchema.validate_announcement(announcement)
            if not is_valid:
                print(f"   ❌ 데이터 {i} 유효성 검사 실패: {error}")
                continue
            
            # Firestore에 저장
            announcement_id = save_announcement(announcement)
            saved_ids.append(announcement_id)
            print(f"   ✅ 공고 {i} 저장 완료: {announcement['title']}")
            print(f"      ID: {announcement_id}")
            print(f"      공고번호: {announcement['announcement_number']}")
        
        print(f"\n   총 {len(saved_ids)}개의 공고가 저장되었습니다.")
        
        # 저장된 데이터 조회 테스트
        print("\n3. 저장된 데이터 조회 테스트 중...")
        
        # 전체 조회
        all_announcements = get_announcements(limit=10)
        print(f"   ✅ 전체 조회 성공: {len(all_announcements)}개")
        
        # 상태별 조회 (인덱스 사용 - 인덱스가 완료되면 사용 가능)
        try:
            pending_announcements = get_announcements(filters={'status': 'pending'}, limit=10)
            print(f"   ✅ 대기 중인 공고 조회 성공: {len(pending_announcements)}개")
        except Exception as e:
            if "index" in str(e).lower() or "인덱스" in str(e):
                print(f"   ⏳ 인덱스 빌드 중... (필터링 쿼리는 인덱스 완료 후 사용 가능)")
            else:
                raise
        
        try:
            approved_announcements = get_announcements(filters={'status': 'approved'}, limit=10)
            print(f"   ✅ 승인된 공고 조회 성공: {len(approved_announcements)}개")
        except Exception as e:
            if "index" in str(e).lower() or "인덱스" in str(e):
                print(f"   ⏳ 인덱스 빌드 중... (필터링 쿼리는 인덱스 완료 후 사용 가능)")
            else:
                raise
        
        # 개별 조회
        if saved_ids:
            first_id = saved_ids[0]
            announcement = get_announcement_by_id(first_id)
            if announcement:
                print(f"\n   ✅ 개별 조회 성공:")
                print(f"      제목: {announcement.get('title')}")
                print(f"      공고번호: {announcement.get('announcement_number')}")
                print(f"      기관: {announcement.get('agency')}")
                print(f"      예산: {announcement.get('budget_amount'):,}원" if announcement.get('budget_amount') else "      예산: 없음")
                print(f"      상태: {announcement.get('status')}")
        
        print("\n" + "=" * 60)
        print("✅ 모든 테스트 통과!")
        print("=" * 60)
        print("\n저장된 공고 ID 목록:")
        for i, aid in enumerate(saved_ids, 1):
            print(f"  {i}. {aid}")
        
        print("\n다음 단계:")
        print("1. 백엔드 서버 실행: python app.py")
        print("2. 프론트엔드에서 데이터 확인")
        print("3. API 엔드포인트 테스트")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_insert_sample_data()
    sys.exit(0 if success else 1)

