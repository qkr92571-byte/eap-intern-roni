"""
Skill: 슬랙 리포트 전송

입력:
    - report_file_path: str (리포트 파일 경로)
    - report_date: datetime (선택, report_file_path가 없을 때 사용)
    - channel_id: str (선택, 기본값: 환경변수 또는 공식 채널)
    - confirm_policy: str ('interactive' 또는 'auto', 기본값: 'interactive')

출력:
    - result: Dict
        - success: bool
        - error: str (실패 시)

부수 효과:
    - 슬랙 전송: 공식 채널에 리포트 메시지 전송
    - 컨펌 정책에 따라 사용자 확인 필요할 수 있음
"""

from datetime import datetime
from typing import Optional, Dict
from pathlib import Path
import os

from services.slack_service import send_report_to_slack
from services.file_service import REPORT_DIR, get_date_string
from utils.constants import SLACK_PRODUCTION_CHANNEL_ID
from orchestration.policies import should_confirm, request_confirmation
from utils.logger import StepLogger


def _choose_slack_channel_interactive() -> Optional[str]:
    """
    슬랙 전송 채널 선택 (대화형)

    옵션:
    1) 공식채널
    2) 테스트 채널
    3) 건너뛰기
    """
    official = os.getenv('SLACK_OFFICIAL_CHANNEL_ID', SLACK_PRODUCTION_CHANNEL_ID)
    test = os.getenv('SLACK_TEST_CHANNEL_ID') or os.getenv('SLACK_CHANNEL_ID')

    print("=" * 60)
    print("슬랙 전송 채널 선택")
    print("=" * 60)
    print(f"1) 공식채널: {official}")
    print(f"2) 테스트 채널: {test or '(미설정)'}")
    print("3) 건너뛰기")
    print()

    choice = input("선택 (1/2/3): ").strip()
    if choice == "1":
        return official
    if choice == "2":
        return test
    return None


def skill_send_slack_report(
    report_file_path: Optional[str] = None,
    report_date: Optional[datetime] = None,
    channel_id: Optional[str] = None,
    confirm_policy: str = 'interactive'
) -> Dict:
    """
    리포트를 슬랙으로 전송
    
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
    logger = StepLogger("스킬: 슬랙 리포트 전송")
    
    try:
        # 리포트 파일 경로 결정
        if report_file_path is None:
            if report_date is None:
                # KST 기준 오늘 날짜
                from datetime import timezone, timedelta
                kst = timezone(timedelta(hours=9))
                report_date = datetime.now(kst)
            
            date_str = get_date_string(report_date)
            report_file_path = str(REPORT_DIR / f'report_{date_str}.json')
        
        report_path = Path(report_file_path)
        if not report_path.exists():
            error_msg = f"리포트 파일을 찾을 수 없습니다: {report_file_path}"
            logger.warning(error_msg)
            return {
                'success': False,
                'error': error_msg
            }

        # 컨펌 정책(대화형)일 때: 채널 선택(공식/테스트/건너뛰기)
        if should_confirm(confirm_policy) and channel_id is None:
            chosen = _choose_slack_channel_interactive()
            if not chosen:
                logger.warning("사용자가 슬랙 전송을 건너뛰었습니다.")
                return {
                    'success': True,
                    'skipped': True,
                    'error': None
                }
            channel_id = chosen

        # 채널 ID 기본값(자동 모드 또는 명시적 채널)
        if channel_id is None:
            channel_id = os.getenv('SLACK_OFFICIAL_CHANNEL_ID', SLACK_PRODUCTION_CHANNEL_ID)
        
        # 채널이 명시된 경우에만 추가 컨펌(선택적으로 유지)
        if should_confirm(confirm_policy) and channel_id is not None:
            logger.warning("선택한 채널로 슬랙 메시지를 전송하시겠습니까?")
            logger.info(f"채널: {channel_id}")
            if not request_confirmation("계속하려면 'yes' 또는 'y'를 입력하세요"):
                logger.warning("사용자가 슬랙 전송을 취소했습니다.")
                return {
                    'success': False,
                    'error': '사용자가 취소했습니다.'
                }
        
        logger.info(f"슬랙 전송 시작: {report_file_path}")
        logger.info(f"채널: {channel_id}")
        
        # 기존 서비스 호출
        success = send_report_to_slack(
            report_file=report_file_path,
            channel_id=channel_id
        )
        
        if success:
            logger.success("슬랙 메시지 전송 완료")
            return {
                'success': True,
                'skipped': False,
                'error': None
            }
        else:
            error_msg = "슬랙 메시지 전송 실패 (환경변수 확인 필요)"
            logger.warning(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
        
    except Exception as e:
        error_msg = f"슬랙 전송 실패: {str(e)}"
        logger.error(error_msg)
        import traceback
        logger.error(traceback.format_exc())
        
        return {
            'success': False,
            'error': error_msg
        }
