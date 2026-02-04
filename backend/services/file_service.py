"""
파일 기반 저장 서비스
- report: 수집 결과 저장
- history: 중복 체크용 히스토리 저장
"""

import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Set
from pathlib import Path

# 프로젝트 루트 디렉토리
PROJECT_ROOT = Path(__file__).parent.parent
REPORT_DIR = PROJECT_ROOT / 'report'
HISTORY_DIR = PROJECT_ROOT / 'history'
# 중복 리포트 저장 디렉토리 (오늘 수집분이 모두 과거 공고인 경우 이력용)
DUPLICATE_REPORT_DIR = PROJECT_ROOT / 'duplicate_reports'

def ensure_directories():
    """필요한 디렉토리 생성"""
    REPORT_DIR.mkdir(exist_ok=True)
    HISTORY_DIR.mkdir(exist_ok=True)
    DUPLICATE_REPORT_DIR.mkdir(exist_ok=True)

def get_date_string(date=None):
    """날짜 문자열 생성 (YYMMDD 형식)"""
    if date is None:
        date = datetime.now()
    return date.strftime('%y%m%d')


def _get_iso_date_string(date=None) -> str:
    """ISO 8601 형식(YYYY-MM-DD)의 날짜 문자열 생성"""
    if date is None:
        date = datetime.now()
    return date.strftime('%Y-%m-%d')

def save_report(announcements: List[Dict], date=None) -> str:
    """
    수집 결과를 report 파일로 저장
    
    Args:
        announcements: 수집된 공고 리스트
        date: 날짜 (기본값: 오늘)
        
    Returns:
        저장된 파일 경로
    """
    ensure_directories()
    
    date_str = get_date_string(date)
    filename = f'report_{date_str}.json'
    filepath = REPORT_DIR / filename
    
    # 기존 파일이 있으면 읽어서 병합 (같은 날 여러번 수집 가능)
    existing_data = []
    if filepath.exists():
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except:
            existing_data = []
    
    # 기존 데이터와 새 데이터 병합 (공고번호 기준 중복 제거)
    existing_numbers = {a.get('announcement_number') for a in existing_data if a.get('announcement_number')}
    new_announcements = [
        a for a in announcements 
        if a.get('announcement_number') and a.get('announcement_number') not in existing_numbers
    ]
    
    merged_data = existing_data + new_announcements
    
    # 파일 저장
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(merged_data, f, ensure_ascii=False, indent=2)
    
    return str(filepath)


def save_duplicate_report(
    duplicates: List[Dict],
    date=None,
    total_duplicates: int | None = None
) -> str:
    """
    중복 공고만 존재하는 경우, 중복 이력을 별도 파일로 저장
    
    - 오늘 수집한 공고 중 모두 과거에 이미 수집된 경우(신규 없음)에 사용
    - 중복 공고의 상세 정보를 그대로 남겨, 나중에 어떤 공고들이 중복이었는지 확인 가능
    
    Args:
        duplicates: 히스토리 기준 중복으로 판정된 공고 리스트
        date: 기준 날짜 (기본값: 오늘)
        total_duplicates: 전체 중복 개수(선택, 없으면 len(duplicates) 사용)
    
    Returns:
        저장된 파일 경로
    """
    ensure_directories()
    
    if not duplicates:
        # 저장할 데이터가 없으면 바로 반환
        date_str = get_date_string(date)
        filename = f'duplicate_report_{date_str}.json'
        filepath = DUPLICATE_REPORT_DIR / filename
        return str(filepath)
    
    date_str_compact = get_date_string(date)
    iso_date = _get_iso_date_string(date)
    filename = f'duplicate_report_{date_str_compact}.json'
    filepath = DUPLICATE_REPORT_DIR / filename
    
    payload = {
        "date": iso_date,
        "generated_at": datetime.now().isoformat(),
        "total_duplicates": int(total_duplicates) if total_duplicates is not None else len(duplicates),
        "announcements": duplicates,
    }
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    
    return str(filepath)

def save_history(announcements: List[Dict], date=None) -> str:
    """
    수집된 공고번호를 history 파일로 저장
    
    Args:
        announcements: 수집된 공고 리스트
        date: 날짜 (기본값: 오늘)
        
    Returns:
        저장된 파일 경로
    """
    ensure_directories()
    
    date_str = get_date_string(date)
    filename = f'history_{date_str}.json'
    filepath = HISTORY_DIR / filename
    
    # 공고번호만 추출
    announcement_numbers = [
        a.get('announcement_number') 
        for a in announcements 
        if a.get('announcement_number')
    ]
    
    # 기존 히스토리 읽기
    existing_numbers = set()
    if filepath.exists():
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                existing_numbers = set(json.load(f))
        except:
            existing_numbers = set()
    
    # 병합
    existing_numbers.update(announcement_numbers)
    
    # 파일 저장
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(list(existing_numbers), f, ensure_ascii=False, indent=2)
    
    return str(filepath)

def get_history_numbers(request_date=None) -> Set[str]:
    """
    요청일 기준 -1일까지의 히스토리에서 공고번호 조회
    
    Args:
        request_date: 요청일 (기본값: 오늘)
        
    Returns:
        공고번호 집합
    """
    ensure_directories()
    
    if request_date is None:
        request_date = datetime.now()
    
    all_numbers = set()
    
    # 요청일 -1일부터 과거로 조회 (요청일 당일은 제외)
    current_date = request_date - timedelta(days=1)
    max_days_back = 30  # 최대 30일 전까지 조회
    
    for i in range(max_days_back):
        date_str = get_date_string(current_date)
        filename = f'history_{date_str}.json'
        filepath = HISTORY_DIR / filename
        
        if filepath.exists():
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    numbers = json.load(f)
                    all_numbers.update(numbers)
            except:
                pass
        
        current_date -= timedelta(days=1)
    
    return all_numbers

def load_report(date=None) -> List[Dict]:
    """
    report 파일에서 데이터 로드
    
    Args:
        date: 날짜 (기본값: 오늘)
        
    Returns:
        공고 리스트
    """
    ensure_directories()
    
    date_str = get_date_string(date)
    filename = f'report_{date_str}.json'
    filepath = REPORT_DIR / filename
    
    if not filepath.exists():
        return []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # 리포트가 딕셔너리 형태인 경우 (slack_sent 등 메타데이터 포함)
            if isinstance(data, dict) and 'announcements' in data:
                return data['announcements']
            # 리포트가 리스트 형태인 경우 (기존 형식)
            elif isinstance(data, list):
                return data
            else:
                return []
    except:
        return []

def check_duplicate_from_history(announcement_number: str, request_date=None) -> bool:
    """
    히스토리 파일에서 중복 체크
    
    Args:
        announcement_number: 공고번호
        request_date: 요청일 (기본값: 오늘)
        
    Returns:
        중복이면 True
    """
    if not announcement_number or not announcement_number.strip():
        return False
    
    history_numbers = get_history_numbers(request_date)
    return announcement_number.strip() in history_numbers

