"""
NotifierAgent: 슬랙 알림 에이전트

역할:
    - 리포트를 슬랙 공식 채널로 전송

보유 스킬:
    - skill_send_slack_report
"""

from datetime import datetime
from typing import Dict, Optional

from skills.slack import skill_send_slack_report
from orchestration.policies import ConfirmPolicy
from utils.logger import StepLogger


class NotifierAgent:
    """슬랙 알림 에이전트"""
    
    def __init__(self):
        self.logger = StepLogger("NotifierAgent")
    
    def send_report(
        self,
        report_file_path: Optional[str] = None,
        report_date: Optional[datetime] = None,
        channel_id: Optional[str] = None,
        confirm_policy: str = ConfirmPolicy.INTERACTIVE.value
    ) -> Dict:
        """
        슬랙 리포트 전송
        
        Args:
            report_file_path: 리포트 파일 경로
            report_date: 리포트 날짜 (report_file_path가 없을 때 사용)
            channel_id: 슬랙 채널 ID (None이면 공식 채널 사용)
            confirm_policy: 컨펌 정책 ('interactive' 또는 'auto')
        
        Returns:
            {
                'success': bool,
                'error': str (실패 시)
            }
        """
        self.logger.info("슬랙 리포트 전송 시작")
        
        result = skill_send_slack_report(
            report_file_path=report_file_path,
            report_date=report_date,
            channel_id=channel_id,
            confirm_policy=confirm_policy
        )
        
        if result.get('success'):
            self.logger.success("슬랙 메시지 전송 완료")
        else:
            self.logger.warning(f"슬랙 전송 실패: {result.get('error')}")
        
        return result
