#!/usr/bin/env python3
"""
Firebase 연결 테스트 스크립트
"""

import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.firebase_service import init_firebase, get_db
from models.announcement_schema import AnnouncementSchema

def test_firebase_connection():
    """Firebase 연결 테스트"""
    print("=" * 50)
    print("Firebase 연결 테스트 시작")
    print("=" * 50)
    
    try:
        # Firebase 초기화
        print("\n1. Firebase 초기화 중...")
        init_firebase()
        print("   ✅ Firebase 초기화 성공")
        
        # Firestore 연결 확인
        print("\n2. Firestore 연결 확인 중...")
        db = get_db()
        print("   ✅ Firestore 연결 성공")
        
        # 테스트 데이터 생성
        print("\n3. 테스트 데이터 생성 중...")
        test_announcement = AnnouncementSchema.create_announcement(
            title="테스트 공고",
            announcement_number="TEST-001",
            agency="테스트 기관",
            budget_amount=1000000,
            estimated_price=900000,
            business_type="일반용역",
            announcement_status="입찰_낙찰제안평가"
        )
        
        # 유효성 검사
        is_valid, error = AnnouncementSchema.validate_announcement(test_announcement)
        if not is_valid:
            print(f"   ❌ 데이터 유효성 검사 실패: {error}")
            return False
        
        print("   ✅ 테스트 데이터 생성 성공")
        print(f"   데이터: {test_announcement}")
        
        # Firestore에 저장 테스트
        print("\n4. Firestore 저장 테스트 중...")
        from services.firebase_service import save_announcement
        announcement_id = save_announcement(test_announcement)
        print(f"   ✅ 저장 성공! 문서 ID: {announcement_id}")
        
        # 저장된 데이터 조회 테스트
        print("\n5. 저장된 데이터 조회 테스트 중...")
        from services.firebase_service import get_announcement_by_id
        retrieved = get_announcement_by_id(announcement_id)
        if retrieved:
            print(f"   ✅ 조회 성공!")
            print(f"   제목: {retrieved.get('title')}")
            print(f"   공고번호: {retrieved.get('announcement_number')}")
            print(f"   기관: {retrieved.get('agency')}")
        else:
            print("   ❌ 조회 실패")
            return False
        
        # 테스트 데이터 삭제
        print("\n6. 테스트 데이터 정리 중...")
        from services.firebase_service import delete_announcement
        delete_announcement(announcement_id)
        print("   ✅ 테스트 데이터 삭제 완료")
        
        print("\n" + "=" * 50)
        print("✅ 모든 테스트 통과!")
        print("=" * 50)
        return True
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_firebase_connection()
    sys.exit(0 if success else 1)


