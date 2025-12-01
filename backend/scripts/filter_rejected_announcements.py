#!/usr/bin/env python3
"""
리포트에서 부적합 공고 제거 스크립트
"""

import sys
import os
import json
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from services.file_service import load_report, REPORT_DIR, get_date_string

def filter_rejected_announcements(report_date=None):
    """
    리포트에서 부적합 공고 제거
    
    Args:
        report_date: 날짜 (기본값: 오늘)
    """
    if report_date is None:
        report_date = datetime.now()
    
    print("=" * 60)
    print("부적합 공고 제거")
    print("=" * 60)
    print(f"날짜: {report_date.strftime('%Y-%m-%d')}\n")
    
    # 리포트 파일 로드
    report_data = load_report(report_date)
    
    if not report_data:
        print("⚠️  리포트 파일이 없습니다.")
        return
    
    print(f"전체 공고 수: {len(report_data)}개\n")
    
    # 부적합 공고 필터링
    approved_announcements = []
    rejected_announcements = []
    
    for announcement in report_data:
        review_result = announcement.get('review_result', '')
        status = announcement.get('status', '')
        
        # 검수 결과에서 "부적합" 키워드 확인 또는 status가 rejected인 경우
        is_rejected = (
            '부적합' in review_result or 
            status == 'rejected' or
            (status == 'approved' and '부적합' in review_result)  # status는 approved지만 검수 결과가 부적합인 경우
        )
        
        if is_rejected:
            rejected_announcements.append(announcement)
        else:
            approved_announcements.append(announcement)
    
    print(f"부적합 공고: {len(rejected_announcements)}개")
    print(f"적합 공고: {len(approved_announcements)}개\n")
    
    if rejected_announcements:
        print("제거될 공고 목록:")
        for i, a in enumerate(rejected_announcements, 1):
            print(f"  [{i}] {a.get('announcement_number', '')} - {a.get('title', '')}")
        print()
    
    # 적합한 공고만 리포트 파일에 저장
    date_str = get_date_string(report_date)
    filename = f'report_{date_str}.json'
    filepath = REPORT_DIR / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(approved_announcements, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 리포트 파일 업데이트 완료: {filepath}")
    print(f"\n최종 결과:")
    print(f"  제거 전: {len(report_data)}개")
    print(f"  제거 후: {len(approved_announcements)}개")
    print(f"  제거된 공고: {len(rejected_announcements)}개")

if __name__ == "__main__":
    filter_rejected_announcements()

