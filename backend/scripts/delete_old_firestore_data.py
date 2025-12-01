#!/usr/bin/env python3
"""
Firestore에서 오늘이 아닌 샘플 데이터 삭제 스크립트
"""

import sys
import os
from datetime import datetime, timedelta

# 프로젝트 루트를 Python 경로에 추가 (backend 디렉토리)
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from services.firebase_service import init_firebase, get_db

def delete_old_data():
    """
    Firestore에서 created_at이 오늘이 아닌 데이터 삭제
    """
    print("=" * 60)
    print("Firestore 샘플 데이터 삭제")
    print("=" * 60)
    
    try:
        # Firebase 초기화
        print("\n1. Firebase 초기화 중...")
        init_firebase()
        db = get_db()
        print("   ✅ Firebase 초기화 성공")
        
        # 오늘 날짜 (시간 제외)
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_str = today.strftime('%Y-%m-%d')
        
        print(f"\n2. 오늘 날짜 기준: {today_str}")
        print("   오늘이 아닌 데이터를 삭제합니다...")
        
        # 모든 공고 조회
        print("\n3. 공고 데이터 조회 중...")
        announcements_ref = db.collection('announcements')
        all_docs = announcements_ref.stream()
        
        deleted_count = 0
        kept_count = 0
        error_count = 0
        
        for doc in all_docs:
            try:
                data = doc.to_dict()
                created_at_str = data.get('created_at', '')
                
                if not created_at_str:
                    # created_at이 없으면 삭제
                    print(f"   삭제: {doc.id} (created_at 없음)")
                    doc.reference.delete()
                    deleted_count += 1
                    continue
                
                # created_at 파싱
                try:
                    # ISO 형식: "2025-12-01T09:40:50.118077" 또는 "2025-12-01T09:40:50"
                    if 'T' in created_at_str:
                        created_at = datetime.fromisoformat(created_at_str.split('.')[0])
                    else:
                        created_at = datetime.fromisoformat(created_at_str)
                    
                    # 날짜만 비교 (시간 제외)
                    created_date = created_at.replace(hour=0, minute=0, second=0, microsecond=0)
                    
                    if created_date < today:
                        # 오늘이 아니면 삭제
                        announcement_number = data.get('announcement_number', 'N/A')
                        print(f"   삭제: {doc.id} ({announcement_number}) - {created_at_str[:10]}")
                        doc.reference.delete()
                        deleted_count += 1
                    else:
                        # 오늘이면 유지
                        kept_count += 1
                        
                except Exception as e:
                    # 파싱 실패 시 삭제
                    print(f"   삭제: {doc.id} (날짜 파싱 실패: {str(e)})")
                    doc.reference.delete()
                    deleted_count += 1
                    
            except Exception as e:
                print(f"   오류: {doc.id} 처리 중 오류 - {str(e)}")
                error_count += 1
                continue
        
        # 결과 출력
        print("\n" + "=" * 60)
        print("삭제 완료!")
        print("=" * 60)
        print(f"삭제된 공고: {deleted_count}개")
        print(f"유지된 공고: {kept_count}개 (오늘 생성)")
        print(f"오류 발생: {error_count}개")
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")
        import traceback
        print(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    # 확인 메시지
    print("⚠️  경고: 이 스크립트는 오늘이 아닌 모든 데이터를 삭제합니다.")
    print("계속하시겠습니까? (yes/no): ", end='')
    
    # 자동 실행을 위해 yes로 설정 (사용자가 명시적으로 요청했으므로)
    response = 'yes'
    print(response)
    
    if response.lower() in ['yes', 'y']:
        delete_old_data()
    else:
        print("취소되었습니다.")

