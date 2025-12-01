#!/usr/bin/env python3
"""
오늘 수집된 리포트를 Firestore에 업로드하는 스크립트
"""

import sys
import os
import json
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가 (backend 디렉토리)
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from services.firebase_service import init_firebase, save_announcement, check_duplicate_announcement
from services.file_service import load_report

def upload_report_to_firestore(report_date=None):
    """
    리포트 파일의 데이터를 Firestore에 업로드
    
    Args:
        report_date: 날짜 (기본값: 오늘)
    """
    if report_date is None:
        report_date = datetime.now()
    
    print("=" * 60)
    print("리포트를 Firestore에 업로드")
    print("=" * 60)
    print(f"날짜: {report_date.strftime('%Y-%m-%d')}")
    
    try:
        # Firebase 초기화
        print("\n1. Firebase 초기화 중...")
        init_firebase()
        print("   ✅ Firebase 초기화 성공")
        
        # 리포트 파일에서 데이터 로드
        print("\n2. 리포트 파일 로드 중...")
        report_data = load_report(report_date)
        
        if not report_data:
            print("   ⚠️  업로드할 데이터가 없습니다.")
            return
        
        print(f"   ✅ 리포트 파일 로드 완료: {len(report_data)}개 공고")
        
        # Firestore에 저장
        print("\n3. Firestore에 업로드 중...")
        uploaded_count = 0
        skipped_count = 0
        failed_count = 0
        
        for idx, announcement in enumerate(report_data, 1):
            try:
                announcement_number = announcement.get('announcement_number', '')
                
                if not announcement_number:
                    print(f"   [{idx}/{len(report_data)}] 공고번호가 없어 건너뜀")
                    skipped_count += 1
                    continue
                
                # 중복 체크
                if check_duplicate_announcement(announcement_number):
                    print(f"   [{idx}/{len(report_data)}] 중복 공고 건너뜀: {announcement_number}")
                    skipped_count += 1
                    continue
                
                # Firestore 스키마에 맞게 데이터 변환
                firestore_data = {
                    'title': announcement.get('title', ''),
                    'announcement_number': announcement_number,
                    'agency': announcement.get('agency', ''),
                    'publish_date': announcement.get('publish_date', ''),
                    'budget_amount': announcement.get('budget_amount'),
                    'estimated_price': announcement.get('estimated_price'),
                    'business_type': announcement.get('business_type'),
                    'created_at': announcement.get('created_at', datetime.now().isoformat()),
                    'source': announcement.get('source', '나라장터'),
                    'status': 'pending',  # 기본 상태
                    'filtered': False,
                    'reviewed': False
                }
                
                # None 값 제거
                firestore_data = {k: v for k, v in firestore_data.items() if v is not None}
                
                # 저장
                doc_id = save_announcement(firestore_data)
                uploaded_count += 1
                
                if idx % 10 == 0:
                    print(f"   진행 중... {idx}/{len(report_data)} (업로드: {uploaded_count}, 건너뜀: {skipped_count})")
                
            except Exception as e:
                print(f"   [{idx}/{len(report_data)}] 업로드 실패: {str(e)}")
                failed_count += 1
                continue
        
        # 결과 출력
        print("\n" + "=" * 60)
        print("업로드 완료!")
        print("=" * 60)
        print(f"전체 공고: {len(report_data)}개")
        print(f"업로드 성공: {uploaded_count}개")
        print(f"건너뜀 (중복): {skipped_count}개")
        print(f"실패: {failed_count}개")
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")
        import traceback
        print(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    # 오늘 날짜로 업로드
    upload_report_to_firestore()

