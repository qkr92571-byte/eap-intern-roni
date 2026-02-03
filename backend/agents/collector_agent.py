"""
CollectorAgent: 공고 수집 에이전트

역할:
    - 나라장터(G2B)에서 키워드 기반 공고 수집
    - 리포트 파일 생성

보유 스킬:
    - skill_scrape_g2b
"""

from datetime import datetime
from typing import List, Dict, Optional

from skills.scrape import skill_scrape_g2b
from utils.logger import StepLogger


class CollectorAgent:
    """공고 수집 에이전트"""
    
    def __init__(self):
        self.logger = StepLogger("CollectorAgent")
    
    def collect(
        self,
        keywords: Optional[List[str]] = None,
        request_date: Optional[datetime] = None
    ) -> Dict:
        """
        공고 수집 실행
        
        Args:
            keywords: 검색할 키워드 리스트 (None이면 Firestore에서 조회)
            request_date: 요청일 (None이면 오늘 KST)
        
        Returns:
            {
                'success': bool,
                'report_file_path': str,
                'collected_count': int,
                'error': str (실패 시)
            }
        """
        self.logger.info("공고 수집 시작")
        
        result = skill_scrape_g2b(
            keywords=keywords,
            request_date=request_date
        )
        
        if result.get('success'):
            self.logger.success(f"수집 완료: {result.get('collected_count', 0)}개")
            self.logger.info(f"리포트 파일: {result.get('report_file_path')}")
        else:
            self.logger.error(f"수집 실패: {result.get('error')}")
        
        return result
