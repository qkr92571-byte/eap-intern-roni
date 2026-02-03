"""
Orchestrator: 워크플로우 오케스트레이터

역할:
    - 사용자 의도를 해석하여 에이전트 호출 순서 결정
    - 컨펌 정책 관리
"""

from datetime import datetime
from typing import Dict, Optional, List
from enum import Enum

from agents.collector_agent import CollectorAgent
from agents.reviewer_agent import ReviewerAgent
from agents.reporter_agent import ReporterAgent
from agents.notifier_agent import NotifierAgent
from orchestration.policies import ConfirmPolicy
from utils.logger import StepLogger


class WorkflowIntent(Enum):
    """워크플로우 의도"""
    DAILY_REPORT = 'daily_report'  # 일일 리포트 생성 (수집 → 검수 → 업로드 → 슬랙)
    REVIEW_ONLY = 'review_only'  # 검수만 실행
    UPLOAD_ONLY = 'upload_only'  # 업로드만 실행
    SLACK_ONLY = 'slack_only'  # 슬랙 전송만 실행
    COLLECT_ONLY = 'collect_only'  # 수집만 실행


class Orchestrator:
    """워크플로우 오케스트레이터"""
    
    def __init__(self, confirm_policy: str = ConfirmPolicy.INTERACTIVE.value):
        """
        Args:
            confirm_policy: 컨펌 정책 ('interactive' 또는 'auto')
        """
        self.confirm_policy = confirm_policy
        self.logger = StepLogger("Orchestrator")
        
        # 에이전트 초기화
        self.collector = CollectorAgent()
        self.reviewer = ReviewerAgent()
        self.reporter = ReporterAgent()
        self.notifier = NotifierAgent()
    
    def execute_daily_report(
        self,
        report_date: Optional[datetime] = None,
        skip_review: bool = False,
        skip_service_items: bool = False,
        skip_slack: bool = False
    ) -> Dict:
        """
        일일 리포트 생성 워크플로우 실행
        
        순서:
        1. 수집 (CollectorAgent)
        2. 검수 (ReviewerAgent, skip_review=True면 스킵)
        3. 서비스 항목 수집 (ReporterAgent, skip_service_items=True면 스킵)
        4. Firestore 업로드 (ReporterAgent)
        5. 슬랙 전송 (NotifierAgent, skip_slack=True면 스킵)
        
        Args:
            report_date: 리포트 날짜 (None이면 오늘 KST)
            skip_review: 검수 단계 건너뛰기
            skip_service_items: 서비스 항목 수집 건너뛰기
            skip_slack: 슬랙 전송 건너뛰기
        
        Returns:
            전체 워크플로우 결과 딕셔너리
        """
        if report_date is None:
            # KST 기준 오늘 날짜
            from datetime import timezone, timedelta
            kst = timezone(timedelta(hours=9))
            report_date = datetime.now(kst)
        
        self.logger.section("일일 리포트 생성 워크플로우 시작")
        self.logger.info(f"날짜: {report_date.strftime('%Y-%m-%d')}")
        self.logger.info(f"컨펌 정책: {self.confirm_policy}")
        
        results = {
            'success': True,
            'report_date': report_date.isoformat(),
            'collect_result': None,
            'review_result': None,
            'service_items_result': None,
            'upload_result': None,
            'slack_result': None,
            'error': None
        }
        
        report_file_path = None
        
        try:
            # 1. 수집
            self.logger.section("[1단계] 공고 수집")
            collect_result = self.collector.collect(request_date=report_date)
            results['collect_result'] = collect_result
            
            if not collect_result.get('success'):
                results['success'] = False
                results['error'] = f"수집 실패: {collect_result.get('error')}"
                return results
            
            report_file_path = collect_result.get('report_file_path')
            collected_count = collect_result.get('collected_count', 0)
            
            if collected_count == 0:
                self.logger.warning("수집된 공고가 없습니다.")
                return results
            
            # 2. 검수
            if not skip_review:
                self.logger.section("[2단계] 공고 검수")
                review_result = self.reviewer.review(
                    report_date=report_date,
                    confirm_policy=self.confirm_policy
                )
                results['review_result'] = review_result
                
                if not review_result.get('success'):
                    results['success'] = False
                    results['error'] = f"검수 실패: {review_result.get('error')}"
                    return results
            else:
                self.logger.info("[2단계] 검수 건너뛰기")
            
            # 3. 서비스 항목 수집
            if not skip_service_items:
                self.logger.section("[3단계] 서비스 항목 수집")
                service_items_result = self.reporter.collect_service_items(
                    report_date=report_date,
                    confirm_policy=self.confirm_policy
                )
                results['service_items_result'] = service_items_result
                
                # 서비스 항목 수집 실패는 치명적이지 않으므로 계속 진행
                if not service_items_result.get('success'):
                    self.logger.warning(f"서비스 항목 수집 실패: {service_items_result.get('error')}")
            else:
                self.logger.info("[3단계] 서비스 항목 수집 건너뛰기")
            
            # 4. Firestore 업로드
            self.logger.section("[4단계] Firestore 업로드")
            upload_result = self.reporter.upload_to_firestore(
                report_date=report_date,
                confirm_policy=self.confirm_policy
            )
            results['upload_result'] = upload_result
            
            if not upload_result.get('success'):
                results['success'] = False
                results['error'] = f"업로드 실패: {upload_result.get('error')}"
                return results
            
            # 5. 슬랙 전송
            if not skip_slack:
                self.logger.section("[5단계] 슬랙 전송")
                slack_result = self.notifier.send_report(
                    report_file_path=report_file_path,
                    report_date=report_date,
                    confirm_policy=self.confirm_policy
                )
                results['slack_result'] = slack_result
                
                # 슬랙 전송 실패는 치명적이지 않으므로 계속 진행
                if not slack_result.get('success'):
                    self.logger.warning(f"슬랙 전송 실패: {slack_result.get('error')}")
            else:
                self.logger.info("[5단계] 슬랙 전송 건너뛰기")
            
            # 최종 결과 출력
            self.logger.section("워크플로우 완료")
            self._print_summary(results)
            
        except Exception as e:
            error_msg = f"워크플로우 실행 중 오류: {str(e)}"
            self.logger.error(error_msg)
            import traceback
            self.logger.error(traceback.format_exc())
            results['success'] = False
            results['error'] = error_msg
        
        return results
    
    def _print_summary(self, results: Dict):
        """결과 요약 출력"""
        self.logger.info("=" * 60)
        self.logger.info("워크플로우 결과 요약")
        self.logger.info("=" * 60)
        
        # 수집 결과
        if results.get('collect_result'):
            cr = results['collect_result']
            self.logger.info(f"[수집] {cr.get('collected_count', 0)}개 공고")
        
        # 검수 결과
        if results.get('review_result'):
            rr = results['review_result']
            self.logger.info(f"[검수] 검수 {rr.get('reviewed_count', 0)}개 / 적합 {rr.get('approved_count', 0)}개 / 부적합 {rr.get('rejected_count', 0)}개")
        
        # 서비스 항목 수집 결과
        if results.get('service_items_result'):
            sir = results['service_items_result']
            self.logger.info(f"[서비스 항목] 처리 {sir.get('processed', 0)}개 / 건너뜀 {sir.get('skipped', 0)}개 / 오류 {sir.get('errors', 0)}개")
        
        # 업로드 결과
        if results.get('upload_result'):
            ur = results['upload_result']
            self.logger.info(f"[업로드] 추가 {ur.get('uploaded', 0)}개 / 업데이트 {ur.get('updated', 0)}개 / 건너뜀 {ur.get('skipped', 0)}개 / 실패 {ur.get('failed', 0)}개")
        
        # 슬랙 결과
        if results.get('slack_result'):
            sr = results['slack_result']
            if sr.get('success'):
                self.logger.info("[슬랙] 전송 완료")
            else:
                self.logger.warning(f"[슬랙] 전송 실패: {sr.get('error')}")
        
        self.logger.info("=" * 60)
