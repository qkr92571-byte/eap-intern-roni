#!/usr/bin/env python3
"""
리포트 검수 및 Firestore 업로드 통합 스크립트

1. 리포트 파일을 ChatGPT API로 검수
2. 검수 결과를 리포트 파일에 반영
3. 검수된 리포트를 Firestore에 업로드
"""

import sys
import os
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가 (backend 디렉토리)
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from services.review_service import review_report_file
from services.firebase_service import init_firebase, save_announcement, check_duplicate_announcement
from services.file_service import load_report

def review_and_upload_report(report_date=None):
    """
    리포트 검수 및 Firestore 업로드 통합 프로세스
    
    Args:
        report_date: 날짜 (기본값: 오늘)
    """
    if report_date is None:
        report_date = datetime.now()
    
    print("=" * 60)
    print("리포트 검수 및 Firestore 업로드")
    print("=" * 60)
    print(f"날짜: {report_date.strftime('%Y-%m-%d')}")
    print()
    
    try:
        # 1단계: 리포트 파일 검수
        print("[1단계] 리포트 파일 검수")
        print("-" * 60)
        review_result = review_report_file(report_date, confirm_before_review=False)
        
        if not review_result.get('success', False):
            print(f"\n❌ 검수 실패: {review_result.get('error', '알 수 없는 오류')}")
            return
        
        print(f"\n✅ 검수 완료!")
        print(f"   검수된 공고: {review_result.get('reviewed_count', 0)}개")
        print(f"   승인: {review_result.get('approved_count', 0)}개")
        print(f"   거부: {review_result.get('rejected_count', 0)}개")
        
        # 2단계: Firebase 초기화
        print("\n[2단계] Firebase 초기화")
        print("-" * 60)
        try:
            init_firebase()
            print("✅ Firebase 초기화 성공")
        except Exception as e:
            print(f"❌ Firebase 초기화 실패: {str(e)}")
            print("   Firebase 키 파일을 확인해주세요.")
            return
        
        # 3단계: 검수된 리포트를 Firestore에 업로드
        print("\n[3단계] Firestore 업로드")
        print("-" * 60)
        
        # 검수된 리포트 파일 로드
        report_data = load_report(report_date)
        
        if not report_data:
            print("⚠️  업로드할 데이터가 없습니다.")
            return
        
        print(f"업로드할 공고: {len(report_data)}개")
        
        uploaded_count = 0
        skipped_count = 0
        failed_count = 0
        
        # 적합/부적합 모두 업로드 (운영진 크로스 체크용)
        approved_count = len([a for a in report_data if a.get('status') == 'approved'])
        rejected_count = len([a for a in report_data if a.get('status') == 'rejected'])
        
        print(f"적합 공고: {approved_count}개")
        print(f"부적합 공고: {rejected_count}개")
        print(f"전체 업로드: {len(report_data)}개 (적합/부적합 모두 포함)")
        
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
                
                # 상태 확인
                status = announcement.get('status', 'pending')
                status_icon = "✅" if status == 'approved' else "❌" if status == 'rejected' else "⏳"
                
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
                    'status': announcement.get('status', 'approved'),  # 검수 결과 반영
                    'filtered': announcement.get('filtered', False),
                    'reviewed': announcement.get('reviewed', True),
                    'review_result': announcement.get('review_result', ''),
                    'review_model': announcement.get('review_model', ''),
                    'reviewed_at': announcement.get('reviewed_at', '')
                }
                
                # None 값 제거
                firestore_data = {k: v for k, v in firestore_data.items() if v is not None}
                
                # 저장
                doc_id = save_announcement(firestore_data)
                uploaded_count += 1
                
                if idx % 10 == 0:
                    print(f"   진행 중... {idx}/{len(report_data)} (업로드: {uploaded_count}, 건너뜀: {skipped_count})")
                else:
                    print(f"   [{idx}/{len(report_data)}] {status_icon} 업로드 ({status}): {announcement_number}")
                
            except Exception as e:
                print(f"   [{idx}/{len(report_data)}] ❌ 업로드 실패: {str(e)}")
                failed_count += 1
                continue
        
        # 최종 결과 출력
        print("\n" + "=" * 60)
        print("전체 프로세스 완료!")
        print("=" * 60)
        print(f"[검수 결과]")
        print(f"  검수된 공고: {review_result.get('reviewed_count', 0)}개")
        print(f"  적합: {review_result.get('approved_count', 0)}개")
        print(f"  부적합: {review_result.get('rejected_count', 0)}개")
        print(f"\n[업로드 결과]")
        print(f"  전체 공고: {len(report_data)}개 (적합/부적합 모두 포함)")
        print(f"  업로드 성공: {uploaded_count}개")
        print(f"  건너뜀 (중복): {skipped_count}개")
        print(f"  실패: {failed_count}개")
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")
        import traceback
        print(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    # 오늘 날짜로 검수 및 업로드
    review_and_upload_report()

