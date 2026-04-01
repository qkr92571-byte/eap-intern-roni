"""
키워드 관리 서비스
"""

from services.firebase_service import get_db
from typing import List

DEFAULT_KEYWORDS = [
    # ── 기존 유지 ────────────────────────────────────────────────
    "찾아가는 상담실",         # 회사 핵심 서비스명
    "심리",                   # 심리지원, 심리치유 등 포착
    "치유",                   # 치유 프로그램 등 포착
    "상담",                   # 심리상담, 상담실 등 포착 (EXCLUSION_KEYWORDS로 노이즈 제거)
    "EAP",                    # Employee Assistance Program

    # ── 신규 추가: 심리/EAP 특화 복합어 ─────────────────────────
    "근로자지원프로그램",       # EAP 한국어 공식 명칭
    "정신건강",                # 정신건강 서비스/증진 사업
    "마음건강",                # 공공기관에서 많이 사용하는 표현
    "전문상담사",              # 전문상담사 파견/배치 공고
    "심리지원단",              # 특정 직군 심리지원단 운영 공고
]

def get_keywords() -> List[str]:
    """저장된 키워드 목록 조회"""
    try:
        db = get_db()
        
        # keywords 컬렉션에서 조회
        keywords_doc = db.collection('settings').document('keywords').get()
        
        if keywords_doc.exists:
            data = keywords_doc.to_dict()
            return data.get('keywords', DEFAULT_KEYWORDS)
        else:
            # 기본 키워드로 초기화
            set_keywords(DEFAULT_KEYWORDS)
            return DEFAULT_KEYWORDS
    except Exception as e:
        print(f"⚠️  Firebase 키워드 조회 실패, 기본 키워드 사용: {str(e)}")
        return DEFAULT_KEYWORDS

def set_keywords(keywords: List[str]) -> bool:
    """키워드 목록 저장"""
    db = get_db()
    
    try:
        # 중복 제거 및 빈 문자열 제거
        keywords = list(set([k.strip() for k in keywords if k.strip()]))
        
        db.collection('settings').document('keywords').set({
            'keywords': keywords,
            'updated_at': None  # Firestore의 서버 타임스탬프 사용
        })
        return True
    except Exception as e:
        print(f"키워드 저장 중 오류: {str(e)}")
        return False

def add_keyword(keyword: str) -> bool:
    """키워드 추가"""
    keywords = get_keywords()
    
    keyword = keyword.strip()
    if not keyword:
        return False
    
    if keyword not in keywords:
        keywords.append(keyword)
        return set_keywords(keywords)
    
    return True  # 이미 존재하는 경우 성공으로 처리

def remove_keyword(keyword: str) -> bool:
    """키워드 삭제"""
    keywords = get_keywords()
    
    if keyword in keywords:
        keywords.remove(keyword)
        return set_keywords(keywords)
    
    return True  # 존재하지 않는 경우 성공으로 처리

def initialize_default_keywords():
    """기본 키워드 초기화"""
    db = get_db()
    
    try:
        keywords_doc = db.collection('settings').document('keywords').get()
        if not keywords_doc.exists:
            set_keywords(DEFAULT_KEYWORDS)
            print(f"기본 키워드 초기화 완료: {DEFAULT_KEYWORDS}")
    except Exception as e:
        print(f"기본 키워드 초기화 중 오류: {str(e)}")


