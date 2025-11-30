"""
나라장터 공고 데이터 스키마 정의

이 모듈은 Firestore에 저장되는 공고 데이터의 구조를 정의합니다.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from utils.constants import STATUS_PENDING, SOURCE_G2B

class AnnouncementSchema:
    """
    나라장터 공고 데이터 스키마
    
    필수 필드:
    - title: 공고명
    - announcement_number: 공고번호
    - agency: 공고기관
    - created_at: 수집일시
    
    선택 필드:
    - budget_amount: 예산금액 (원 단위 숫자)
    - estimated_price: 추정가격 (원 단위 숫자)
    - business_type: 사업구분
    - announcement_status: 공고상태 (나라장터 원본 상태)
    - deadline: 마감일
    - url: 원본 링크
    - content: 공고 내용
    - category: 카테고리
    
    시스템 필드:
    - status: 시스템 내부 상태 (pending, approved, rejected)
    - filtered: 필터링 여부
    - reviewed: 검수 여부
    - review_result: 검수 결과 (ChatGPT)
    - source: 출처 (기본값: '나라장터')
    """
    
    # 필수 필드
    REQUIRED_FIELDS = [
        'title',
        'announcement_number',
        'agency',
        'created_at'
    ]
    
    # 선택 필드
    OPTIONAL_FIELDS = [
        'budget_amount',
        'estimated_price',
        'business_type',
        'announcement_status',
        'deadline',
        'url',
        'content',
        'category'
    ]
    
    # 시스템 필드
    SYSTEM_FIELDS = [
        'status',
        'filtered',
        'reviewed',
        'review_result',
        'source'
    ]
    
    @staticmethod
    def create_announcement(
        title: str,
        announcement_number: str,
        agency: str,
        budget_amount: Optional[int] = None,
        estimated_price: Optional[int] = None,
        business_type: Optional[str] = None,
        announcement_status: Optional[str] = None,
        deadline: Optional[str] = None,
        url: Optional[str] = None,
        content: Optional[str] = None,
        category: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        공고 데이터 생성
        
        Args:
            title: 공고명
            announcement_number: 공고번호
            agency: 공고기관
            budget_amount: 예산금액 (원 단위 숫자, 예: 150704000)
            estimated_price: 추정가격 (원 단위 숫자, 예: 137003636)
            business_type: 사업구분 (예: '일반용역')
            announcement_status: 공고상태 (예: '입찰_낙찰제안평가')
            deadline: 마감일 (ISO 형식 또는 문자열)
            url: 원본 링크
            content: 공고 내용
            category: 카테고리
            **kwargs: 기타 추가 필드
            
        Returns:
            공고 데이터 딕셔너리
        """
        announcement = {
            # 필수 필드
            'title': title,
            'announcement_number': announcement_number,
            'agency': agency,
            'created_at': datetime.now().isoformat(),
            
            # 선택 필드
            'budget_amount': budget_amount,
            'estimated_price': estimated_price,
            'business_type': business_type,
            'announcement_status': announcement_status,
            'deadline': deadline,
            'url': url,
            'content': content,
            'category': category,
            
            # 시스템 필드 (기본값)
            'status': STATUS_PENDING,  # pending, approved, rejected
            'filtered': False,
            'reviewed': False,
            'source': SOURCE_G2B
        }
        
        # 추가 필드 병합
        announcement.update(kwargs)
        
        # None 값 제거 (선택사항)
        announcement = {k: v for k, v in announcement.items() if v is not None}
        
        return announcement
    
    @staticmethod
    def parse_budget_string(budget_str: str) -> Optional[int]:
        """
        예산 문자열을 숫자로 변환
        예: "150,704,000원" -> 150704000
        
        Args:
            budget_str: 예산 문자열
            
        Returns:
            예산 금액 (원 단위 숫자) 또는 None
        """
        if not budget_str:
            return None
        
        # 쉼표와 "원" 제거
        budget_str = budget_str.replace(',', '').replace('원', '').replace(' ', '').strip()
        
        try:
            return int(budget_str)
        except ValueError:
            return None
    
    @staticmethod
    def validate_announcement(data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        공고 데이터 유효성 검사
        
        Args:
            data: 검사할 공고 데이터
            
        Returns:
            (유효성 여부, 오류 메시지)
        """
        # 필수 필드 확인
        for field in AnnouncementSchema.REQUIRED_FIELDS:
            if field not in data or not data[field]:
                return False, f"필수 필드 '{field}'가 없거나 비어있습니다."
        
        # 예산 금액이 문자열인 경우 숫자로 변환 시도
        if 'budget_amount' in data and isinstance(data['budget_amount'], str):
            parsed = AnnouncementSchema.parse_budget_string(data['budget_amount'])
            if parsed is not None:
                data['budget_amount'] = parsed
        
        if 'estimated_price' in data and isinstance(data['estimated_price'], str):
            parsed = AnnouncementSchema.parse_budget_string(data['estimated_price'])
            if parsed is not None:
                data['estimated_price'] = parsed
        
        return True, None

# 스키마 예시 데이터
EXAMPLE_ANNOUNCEMENT = {
    'title': '2026년 찾아가는 상담실 운영',
    'announcement_number': 'R25BK01187770',
    'agency': '제주특별자치도 소방안전본부',
    'budget_amount': 150704000,  # 150,704,000원
    'estimated_price': 137003636,  # 137,003,636원
    'business_type': '일반용역',
    'announcement_status': '입찰_낙찰제안평가',
    'status': 'pending',
    'filtered': False,
    'reviewed': False,
    'created_at': datetime.now().isoformat(),
    'source': '나라장터'
}

