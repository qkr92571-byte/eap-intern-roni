"""
ReporterAgent: 리포트 반영 에이전트

역할:
    - Firestore에 리포트 데이터 업로드(Upsert)
    - 적합 공고의 첨부파일 조사 및 서비스 항목 수집

보유 스킬:
    - skill_upsert_firestore
    - skill_collect_service_items
"""

from datetime import datetime
from typing import Dict, Optional

from skills.firestore import skill_upsert_firestore
from skills.service_items import skill_collect_service_items
from orchestration.policies import ConfirmPolicy
from utils.logger import StepLogger


class ReporterAgent:
    """리포트 반영 에이전트"""
    
    def __init__(self):
        self.logger = StepLogger("ReporterAgent")
    
    def upload_to_firestore(
        self,
        report_date: Optional[datetime] = None,
        report_data: Optional[list] = None,
        confirm_policy: str = ConfirmPolicy.INTERACTIVE.value
    ) -> Dict:
        """
        Firestore에 리포트 업로드
        
        Args:
            report_date: 리포트 날짜 (report_data가 없을 때 사용)
            report_data: 공고 데이터 리스트 (report_date가 없을 때 사용)
            confirm_policy: 컨펌 정책 ('interactive' 또는 'auto')
        
        Returns:
            {
                'success': bool,
                'uploaded': int,
                'updated': int,
                'skipped': int,
                'failed': int,
                'error': str (실패 시)
            }
        """
        self.logger.info("Firestore 업로드 시작")
        
        result = skill_upsert_firestore(
            report_date=report_date,
            report_data=report_data,
            confirm_policy=confirm_policy
        )
        
        if result.get('success'):
            self.logger.success("업로드 완료")
            self.logger.info(f"추가: {result.get('uploaded', 0)}개")
            self.logger.info(f"업데이트: {result.get('updated', 0)}개")
            self.logger.info(f"건너뜀: {result.get('skipped', 0)}개")
            self.logger.info(f"실패: {result.get('failed', 0)}개")
        else:
            self.logger.error(f"업로드 실패: {result.get('error')}")
        
        return result
    
    def collect_service_items(
        self,
        report_date: Optional[datetime] = None,
        confirm_policy: str = ConfirmPolicy.INTERACTIVE.value
    ) -> Dict:
        """
        적합 공고의 첨부파일 조사 및 서비스 항목 수집
        
        Args:
            report_date: 리포트 날짜 (None이면 오늘 KST)
            confirm_policy: 컨펌 정책 ('interactive' 또는 'auto')
        
        Returns:
            {
                'success': bool,
                'processed': int,
                'skipped': int,
                'errors': int,
                'error': str (실패 시)
            }
        """
        self.logger.info("서비스 항목 수집 시작")
        
        result = skill_collect_service_items(
            report_date=report_date,
            confirm_policy=confirm_policy
        )
        
        if result.get('success'):
            self.logger.success("서비스 항목 수집 완료")
            self.logger.info(f"처리 완료: {result.get('processed', 0)}개")
            self.logger.info(f"건너뜀: {result.get('skipped', 0)}개")
            self.logger.info(f"오류: {result.get('errors', 0)}개")
        else:
            self.logger.warning(f"서비스 항목 수집 중 오류: {result.get('error')}")
        
        return result
