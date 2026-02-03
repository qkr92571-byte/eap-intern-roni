"""
ReviewerAgent: 공고 검수 에이전트

역할:
    - 리포트 파일의 공고들을 ChatGPT API로 적합/부적합 검수
    - 리포트 파일 업데이트

보유 스킬:
    - skill_review_announcements
"""

from datetime import datetime
from typing import Dict, Optional

from skills.review import skill_review_announcements
from orchestration.policies import ConfirmPolicy
from utils.logger import StepLogger


class ReviewerAgent:
    """공고 검수 에이전트"""
    
    def __init__(self):
        self.logger = StepLogger("ReviewerAgent")
    
    def review(
        self,
        report_date: Optional[datetime] = None,
        confirm_policy: str = ConfirmPolicy.INTERACTIVE.value
    ) -> Dict:
        """
        공고 검수 실행
        
        Args:
            report_date: 리포트 날짜 (None이면 오늘 KST)
            confirm_policy: 컨펌 정책 ('interactive' 또는 'auto')
        
        Returns:
            {
                'success': bool,
                'reviewed_count': int,
                'approved_count': int,
                'rejected_count': int,
                'error': str (실패 시)
            }
        """
        self.logger.info("공고 검수 시작")
        
        # confirm_policy에 따라 confirm_before_review 결정
        confirm_before_review = (confirm_policy == ConfirmPolicy.INTERACTIVE.value)
        
        result = skill_review_announcements(
            report_date=report_date,
            confirm_before_review=confirm_before_review
        )
        
        if result.get('success'):
            self.logger.success("검수 완료")
            self.logger.info(f"검수된 공고: {result.get('reviewed_count', 0)}개")
            self.logger.info(f"적합: {result.get('approved_count', 0)}개")
            self.logger.info(f"부적합: {result.get('rejected_count', 0)}개")
        else:
            self.logger.error(f"검수 실패: {result.get('error')}")
        
        return result
