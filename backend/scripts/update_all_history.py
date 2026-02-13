"""
모든 리포트를 검토하여 history 파일에 누락된 공고번호 추가
"""

import json
import sys
from pathlib import Path
from typing import Set, Dict
from collections import defaultdict

# 프로젝트 루트를 경로에 추가
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from services.file_service import REPORT_DIR, HISTORY_DIR, get_date_string
from datetime import datetime

def extract_announcement_numbers(report_data) -> Set[str]:
    """리포트 데이터에서 공고번호 추출"""
    numbers = set()
    
    if isinstance(report_data, list):
        announcements = report_data
    elif isinstance(report_data, dict):
        announcements = report_data.get('announcements', [])
    else:
        return numbers
    
    for ann in announcements:
        ann_number = ann.get('announcement_number')
        if ann_number and ann_number.strip():
            numbers.add(ann_number.strip())
    
    return numbers

def update_history_file(date_str: str, announcement_numbers: Set[str]) -> tuple[int, int]:
    """
    history 파일 업데이트
    
    Returns:
        (기존 개수, 추가된 개수) 튜플
    """
    history_file = HISTORY_DIR / f'history_{date_str}.json'
    
    # 기존 history 읽기
    existing_numbers = set()
    if history_file.exists():
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                if isinstance(existing_data, list):
                    existing_numbers = set(existing_data)
        except Exception as e:
            print(f"  ⚠️  기존 history 파일 읽기 실패: {str(e)}")
    
    existing_count = len(existing_numbers)
    
    # 새 공고번호 추가
    existing_numbers.update(announcement_numbers)
    
    new_count = len(existing_numbers) - existing_count
    
    # 파일 저장
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(sorted(list(existing_numbers)), f, ensure_ascii=False, indent=2)
    
    return existing_count, new_count

def main():
    print("=" * 60)
    print("모든 리포트 검토 및 History 업데이트")
    print("=" * 60)
    print()
    
    # 리포트 파일 목록 가져오기
    report_files = sorted(REPORT_DIR.glob('report_*.json'))
    
    if not report_files:
        print("❌ 리포트 파일이 없습니다.")
        return 1
    
    print(f"발견된 리포트 파일: {len(report_files)}개")
    print()
    
    # 날짜별로 공고번호 수집
    date_to_numbers: Dict[str, Set[str]] = defaultdict(set)
    total_announcements = 0
    processed_files = 0
    
    for report_file in report_files:
        try:
            # 날짜 추출 (report_YYMMDD.json)
            date_str = report_file.stem.replace('report_', '')
            
            # 리포트 파일 읽기
            with open(report_file, 'r', encoding='utf-8') as f:
                report_data = json.load(f)
            
            # 공고번호 추출
            numbers = extract_announcement_numbers(report_data)
            
            if numbers:
                date_to_numbers[date_str].update(numbers)
                total_announcements += len(numbers)
                processed_files += 1
                print(f"✅ {report_file.name}: {len(numbers)}개 공고")
            else:
                print(f"⚠️  {report_file.name}: 공고번호 없음")
        
        except Exception as e:
            print(f"❌ {report_file.name} 처리 실패: {str(e)}")
            continue
    
    print()
    print(f"처리된 리포트: {processed_files}개")
    print(f"총 공고 수: {total_announcements}개")
    print()
    
    # History 파일 업데이트
    print("=" * 60)
    print("History 파일 업데이트")
    print("=" * 60)
    print()
    
    total_existing = 0
    total_added = 0
    updated_files = 0
    
    for date_str, numbers in sorted(date_to_numbers.items()):
        existing_count, added_count = update_history_file(date_str, numbers)
        total_existing += existing_count
        total_added += added_count
        
        if added_count > 0:
            updated_files += 1
            print(f"✅ history_{date_str}.json: 기존 {existing_count}개, 추가 {added_count}개 (총 {existing_count + added_count}개)")
        else:
            print(f"ℹ️  history_{date_str}.json: 변경 없음 (총 {existing_count}개)")
    
    print()
    print("=" * 60)
    print("요약")
    print("=" * 60)
    print(f"처리된 리포트: {processed_files}개")
    print(f"업데이트된 History 파일: {updated_files}개")
    print(f"기존 공고번호: {total_existing}개")
    print(f"추가된 공고번호: {total_added}개")
    print()
    
    # 누락 확인
    print("=" * 60)
    print("누락 확인")
    print("=" * 60)
    
    missing_found = False
    for date_str, numbers in sorted(date_to_numbers.items()):
        history_file = HISTORY_DIR / f'history_{date_str}.json'
        
        if not history_file.exists():
            print(f"❌ history_{date_str}.json 파일이 없습니다!")
            missing_found = True
            continue
        
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                history_numbers = set(json.load(f))
            
            missing = numbers - history_numbers
            if missing:
                print(f"⚠️  {date_str}: {len(missing)}개 공고번호 누락")
                for num in sorted(missing):
                    print(f"     - {num}")
                missing_found = True
            else:
                print(f"✅ {date_str}: 누락 없음")
        
        except Exception as e:
            print(f"❌ {date_str}: 확인 실패 - {str(e)}")
            missing_found = True
    
    if not missing_found:
        print("✅ 모든 공고번호가 history에 정상적으로 포함되어 있습니다!")
    
    return 0 if not missing_found else 1

if __name__ == '__main__':
    sys.exit(main())
