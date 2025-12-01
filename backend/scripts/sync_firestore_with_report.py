#!/usr/bin/env python3
"""
리포트 파일 기준으로 Firestore 동기화
- 리포트에 있는 적합한 공고는 Firestore에 업데이트/추가
- 리포트에 없는 공고(부적합으로 제외된 공고)는 Firestore에서 삭제
"""

import sys
import os
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from services.firebase_service import (
    init_firebase,
    get_db,
    get_announcements,
    save_announcement,
    delete_announcement,
    check_duplicate_announcement
)
from services.file_service import load_report

def get_announcement_by_number(announcement_number: str):
    """
    공고번호로 Firestore에서 공고 조회
    
    Args:
        announcement_number: 공고번호
    
    Returns:
        공고 문서 ID와 데이터, 없으면 None
    """
    db = get_db()
    query = db.collection('announcements').where('announcement_number', '==', announcement_number.strip()).limit(1)
    docs = list(query.stream())
    
    if docs:
        doc = docs[0]
        return {
            'id': doc.id,
            'data': doc.to_dict()
        }
    return None

def sync_firestore_with_report(report_date=None):
    """
    리포트 파일 기준으로 Firestore 동기화
    
    Args:
        report_date: 날짜 (기본값: 오늘)
    """
    if report_date is None:
        report_date = datetime.now()
    
    print("=" * 60)
    print("Firestore 동기화 (리포트 기준)")
    print("=" * 60)
    print(f"날짜: {report_date.strftime('%Y-%m-%d')}\n")
    
    try:
        # Firebase 초기화
        print("[1단계] Firebase 초기화")
        print("-" * 60)
        init_firebase()
        print("✅ Firebase 초기화 성공\n")
        
        # 리포트 파일 로드
        print("[2단계] 리포트 파일 로드")
        print("-" * 60)
        report_data = load_report(report_date)
        
        if not report_data:
            print("⚠️  리포트 파일이 없습니다.")
            return
        
        print(f"✅ 리포트 파일 로드 완료: {len(report_data)}개 공고\n")
        
        # 리포트에 있는 공고번호 목록
        report_numbers = {
            a.get('announcement_number', '').strip() 
            for a in report_data 
            if a.get('announcement_number', '').strip()
        }
        
        print(f"리포트에 있는 공고번호: {len(report_numbers)}개\n")
        
        # Firestore에서 오늘 날짜의 공고 조회
        print("[3단계] Firestore에서 공고 조회")
        print("-" * 60)
        
        # created_at이 오늘 날짜인 공고 조회 (날짜 문자열로 비교)
        today_str = report_date.strftime('%Y-%m-%d')
        db = get_db()
        
        # 모든 공고 조회 (날짜 필터링은 나중에)
        all_firestore_announcements = []
        query = db.collection('announcements').stream()
        
        for doc in query:
            data = doc.to_dict()
            data['id'] = doc.id
            # created_at이 오늘 날짜로 시작하는지 확인
            created_at = data.get('created_at', '')
            if created_at.startswith(today_str):
                all_firestore_announcements.append(data)
        
        print(f"✅ Firestore에서 오늘 날짜 공고 조회 완료: {len(all_firestore_announcements)}개\n")
        
        # Firestore에 있는 공고번호 목록
        firestore_numbers = {
            a.get('announcement_number', '').strip() 
            for a in all_firestore_announcements 
            if a.get('announcement_number', '').strip()
        }
        
        # 삭제할 공고 (Firestore에는 있지만 리포트에는 없는 공고)
        to_delete = firestore_numbers - report_numbers
        
        # 추가/업데이트할 공고 (리포트에는 있지만 Firestore에는 없거나 업데이트 필요한 공고)
        to_add_or_update = report_numbers
        
        print("[4단계] 부적합 공고 삭제")
        print("-" * 60)
        deleted_count = 0
        
        for announcement_number in to_delete:
            try:
                # 공고번호로 문서 찾기
                announcement_info = get_announcement_by_number(announcement_number)
                if announcement_info:
                    delete_announcement(announcement_info['id'])
                    deleted_count += 1
                    print(f"  ✅ 삭제: {announcement_number}")
            except Exception as e:
                print(f"  ❌ 삭제 실패 ({announcement_number}): {str(e)}")
        
        print(f"\n삭제 완료: {deleted_count}개\n")
        
        # 리포트의 공고를 Firestore에 추가/업데이트 (적합/부적합 모두 포함)
        print("[5단계] 공고 추가/업데이트 (적합/부적합 모두 포함)")
        print("-" * 60)
        added_count = 0
        updated_count = 0
        skipped_count = 0
        
        for announcement in report_data:
            try:
                announcement_number = announcement.get('announcement_number', '').strip()
                
                if not announcement_number:
                    skipped_count += 1
                    continue
                
                # Firestore에 이미 있는지 확인
                existing = get_announcement_by_number(announcement_number)
                
                # Firestore 스키마에 맞게 데이터 변환
                firestore_data = {
                    'title': announcement.get('title', ''),
                    'announcement_number': announcement_number,
                    'agency': announcement.get('agency', ''),
                    'publish_date': announcement.get('publish_date', ''),
                    'budget_amount': announcement.get('budget_amount'),
                    'estimated_price': announcement.get('estimated_price'),
                    'business_type': announcement.get('business_type', ''),
                    'created_at': announcement.get('created_at', datetime.now().isoformat()),
                    'source': announcement.get('source', '나라장터'),
                    'status': announcement.get('status', 'approved'),
                    'filtered': announcement.get('filtered', False),
                    'reviewed': announcement.get('reviewed', True),
                    'review_result': announcement.get('review_result', ''),
                    'review_model': announcement.get('review_model', ''),
                    'reviewed_at': announcement.get('reviewed_at', '')
                }
                
                # None 값 제거
                firestore_data = {k: v for k, v in firestore_data.items() if v is not None}
                
                if existing:
                    # 업데이트
                    db.collection('announcements').document(existing['id']).update(firestore_data)
                    updated_count += 1
                    print(f"  ✅ 업데이트: {announcement_number}")
                else:
                    # 추가
                    save_announcement(firestore_data)
                    added_count += 1
                    print(f"  ✅ 추가: {announcement_number}")
                
            except Exception as e:
                print(f"  ❌ 처리 실패 ({announcement.get('announcement_number', '')}): {str(e)}")
                skipped_count += 1
                continue
        
        # 최종 결과 출력
        print("\n" + "=" * 60)
        print("동기화 완료!")
        print("=" * 60)
        print(f"[삭제]")
        print(f"  부적합 공고 삭제: {deleted_count}개")
        print(f"\n[추가/업데이트]")
        print(f"  추가: {added_count}개")
        print(f"  업데이트: {updated_count}개")
        print(f"  건너뜀: {skipped_count}개")
        print(f"\n[최종 상태]")
        print(f"  리포트 공고: {len(report_data)}개")
        print(f"  Firestore 공고 (오늘 날짜): {len(all_firestore_announcements) - deleted_count + added_count}개")
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")
        import traceback
        print(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    sync_firestore_with_report()

