"""
EAP 공고 제목 기반 1단계 필터
- EXCLUSION_KEYWORDS: 제목에 포함 시 자동 부적합 처리
- FAST_APPROVE_PATTERNS: 제목만으로 명확히 적합 판단 가능한 패턴
"""
from typing import Dict, List, Tuple

EXCLUSION_KEYWORDS: List[str] = [
    # ── 기존 유지 ────────────────────────────────────────
    '콜센터',
    '차량 임차',
    '차량임차',
    '운행',
    '통근버스',
    '통근 버스',
    '버스 운행',
    '버스운행',
    '근로자 파견',

    # ── 취업/진로/직업 상담 (비심리적) ───────────────────
    '취업상담',
    '취업 상담',
    '직업상담',
    '직업 상담',
    '진로상담',
    '진로 상담',
    '진학상담',
    '진학 상담',
    '취업성공',           # 취업성공디딤돌 등 취업지원 사업

    # ── 세무/법률/금융 상담 (비심리적) ───────────────────
    '세무상담',
    '세무 상담',
    '법률상담',
    '법률 상담',
    '소득세',             # 종합소득세 홈택스 임시상담 등

    # ── 농업/수출/가맹 상담 (비심리적) ───────────────────
    '수출상담',
    '수출 상담',
    '바이어 상담',
    '가맹상담',
    '창업상담',
    '주거상담',
    '주거 상담',

    # ── IT 상담시스템 유지보수 ────────────────────────────
    '상담시스템 유지보수',
    '상담 시스템 유지보수',

    # ── 상담사 자격시험 ───────────────────────────────────
    '자격시험',
    '상담사 자격',

    # ── 고객서비스 품질관리 ───────────────────────────────
    '전화상담 품질',
    '고객만족도 조사',

    # ── 관광/통역 ─────────────────────────────────────────
    '관광통역',
]

FAST_APPROVE_PATTERNS = [
    # ── 기존 유지 ────────────────────────────────────────────────
    {'keyword': '찾아가는 상담실',         'exceptions': ['개발', '구축', '시스템']},
    {'keyword': '근로자지원프로그램(EAP)',  'exceptions': ['개발', '구축']},
    {'keyword': 'EAP 운영',               'exceptions': ['개발', '구축']},

    # ── EAP 직접 표기 변형 ────────────────────────────────────────
    {'keyword': 'EAP운영',                'exceptions': ['개발', '구축']},
    {'keyword': '근로자지원프로그램 운영', 'exceptions': ['개발', '구축']},

    # ── 심리상담 서비스 직접 표기 ─────────────────────────────────
    {'keyword': '심리상담 위탁',           'exceptions': ['개발', '구축', '시스템']},
    {'keyword': '심리상담 용역',           'exceptions': ['개발', '구축', '시스템']},
    {'keyword': '심리상담 운영',           'exceptions': ['개발', '구축', '시스템']},
    {'keyword': '전문심리상담',            'exceptions': ['개발', '구축', '시스템']},

    # ── 학생/청소년 정서 관련 ─────────────────────────────────────
    {'keyword': '정서행동특성검사',        'exceptions': ['개발', '구축', '시스템']},

    # ── 특수 심리지원 ─────────────────────────────────────────────
    {'keyword': '심리지원 시범',           'exceptions': ['개발', '구축']},
    {'keyword': '마음이음',               'exceptions': ['개발', '구축']},

    # ── 인력 파견형 EAP ───────────────────────────────────────────
    {'keyword': '전문상담사 파견',         'exceptions': ['개발', '구축']},
    {'keyword': '심리상담사 파견',         'exceptions': ['개발', '구축']},

    # ── 소방/공무원 심리지원 ──────────────────────────────────────
    {'keyword': '소방공무원 마음',         'exceptions': ['개발', '구축']},
    {'keyword': '마음건강 설문',           'exceptions': ['개발', '구축', '시스템']},
]


def should_exclude_by_keywords(announcement: Dict) -> Tuple[bool, str]:
    """
    제외 키워드로 인한 자동 부적합 판단

    Returns:
        (제외 여부, 제외 사유) 튜플
    """
    title = announcement.get('title', '').lower()
    for keyword in EXCLUSION_KEYWORDS:
        if keyword.lower() in title:
            return True, f"제외 키워드 포함: '{keyword}'"
    return False, ""


def classify_by_title(announcement: Dict) -> str:
    """
    제목 기반 빠른 분류 (1단계 필터)

    Returns:
        'rejected'  - 제외 키워드 hit → 첨부파일 불필요
        'approved'  - 명확 EAP 키워드 hit → 첨부파일 불필요
        'uncertain' - 판단 불가 → 2단계(GPT) 필요
    """
    exclude, _ = should_exclude_by_keywords(announcement)
    if exclude:
        return 'rejected'

    title = announcement.get('title', '')
    for pattern in FAST_APPROVE_PATTERNS:
        if pattern['keyword'] in title:
            if not any(exc in title for exc in pattern['exceptions']):
                return 'approved'

    return 'uncertain'
