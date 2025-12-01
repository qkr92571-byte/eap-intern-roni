#!/usr/bin/env python3
"""
리포트 검수 사이클 실행 (데이터 수집 제외)

1. 리포트 파일 로드
2. AI 검수
3. 부적합 공고 제거
4. Firestore 동기화 (선택사항)
"""

import sys
import os
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from services.review_service import review_report_file
from services.file_service import load_report
from scripts.sync_firestore_with_report import sync_firestore_with_report

def run_review_cycle(update_firestore=False):
    """
    리포트 검수 사이클 실행
    
    Args:
        update_firestore: Firestore 업데이트 여부 (기본값: False)
    """
    print("=" * 60)
    print("리포트 검수 사이클 실행")
    print("=" * 60)
    print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    try:
        request_date = datetime.now()
        
        # 리포트 파일 확인
        report_data = load_report(request_date)
        if not report_data:
            print("⚠️  리포트 파일이 없습니다.")
            print("   먼저 데이터 수집을 실행해주세요.")
            return
        
        print(f"리포트 파일 로드: {len(report_data)}개 공고\n")
        
        # 1단계: 리포트 검수
        print("[1단계] 리포트 검수 (ChatGPT API)")
        print("-" * 60)
        print("⚠️  ChatGPT API 사용 시 비용이 발생합니다.")
        print(f"   검수할 공고 수: {len(report_data)}개")
        print(f"   예상 비용: 약 ${len(report_data) * 0.002:.2f} (gpt-3.5-turbo 기준)")
        print("   검수를 진행합니다...\n")
        # 스크립트 실행 시에는 이미 사용자가 명시적으로 실행했으므로 별도 입력 없이 진행
        review_result = review_report_file(request_date, confirm_before_review=False)
        
        if not review_result.get('success', False):
            print(f"\n❌ 검수 실패: {review_result.get('error', '알 수 없는 오류')}")
            return
        
        print(f"\n✅ 검수 완료!")
        print(f"   검수된 공고: {review_result.get('reviewed_count', 0)}개")
        print(f"   적합: {review_result.get('approved_count', 0)}개")
        print(f"   부적합: {review_result.get('rejected_count', 0)}개\n")
        
        # 최종 리포트 확인 (적합/부적합 모두 유지)
        final_report = load_report(request_date)
        print(f"\n✅ 최종 리포트: {len(final_report)}개 공고 (적합/부적합 모두 포함)\n")
        
        # 2단계: Firestore 동기화 (선택사항)
        if update_firestore:
            print("[3단계] Firestore 동기화")
            print("-" * 60)
            sync_firestore_with_report(request_date)
        else:
            print("[3단계] Firestore 동기화")
            print("-" * 60)
            print("⚠️  Firestore 업데이트는 건너뜁니다.")
            print("   업데이트하려면 --update-firestore 플래그를 사용하세요.\n")
        
        # 최종 요약
        print("=" * 60)
        print("검수 사이클 완료!")
        print("=" * 60)
        print(f"검수 완료: {review_result.get('reviewed_count', 0)}개")
        print(f"승인: {review_result.get('approved_count', 0)}개")
        print(f"거부: {review_result.get('rejected_count', 0)}개")
        print(f"최종 리포트: {len(final_report)}개")
        if update_firestore:
            print(f"Firestore: 동기화 완료")
        print(f"\n완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")
        import traceback
        print(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='리포트 검수 사이클 실행')
    parser.add_argument(
        '--update-firestore',
        action='store_true',
        help='Firestore 업데이트 포함'
    )
    
    args = parser.parse_args()
    run_review_cycle(update_firestore=args.update_firestore)

