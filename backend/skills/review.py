"""
Skill: 공고 적합/부적합 검수

입력:
    - report_date: datetime (선택, 기본값: 오늘 KST)
    - confirm_before_review: bool (검수 전 사용자 컨펌, 기본값: True)

출력:
    - result: Dict
        - success: bool
        - reviewed_count: int
        - approved_count: int
        - rejected_count: int
        - error: str (실패 시)

부수 효과:
    - 파일 쓰기: backend/report/report_YYMMDD.json 업데이트 (status, review_* 필드 추가)
"""

from datetime import datetime
from typing import Dict, Optional

from services.review_service import review_report_file
from utils.logger import StepLogger


def skill_review_announcements(
    report_date: Optional[datetime] = None,
    confirm_before_review: bool = True
) -> Dict:
    """
    리포트 파일의 공고들을 ChatGPT API로 적합/부적합 검수
    
    Args:
        report_date: 리포트 날짜 (None이면 오늘 KST)
        confirm_before_review: 검수 전 사용자 컨펌 받기
    
    Returns:
        {
            'success': bool,
            'reviewed_count': int,
            'approved_count': int,
            'rejected_count': int,
            'error': str (실패 시)
        }
    """
    logger = StepLogger("스킬: 공고 검수")
    
    try:
        if report_date is None:
            # KST 기준 오늘 날짜
            from datetime import timezone, timedelta
            kst = timezone(timedelta(hours=9))
            report_date = datetime.now(kst)
        
        logger.info(f"날짜: {report_date.strftime('%Y-%m-%d')}")
        logger.info(f"컨펌 필요: {confirm_before_review}")
        
        # 기존 서비스 호출
        result = review_report_file(
            report_date=report_date,
            confirm_before_review=confirm_before_review
        )
        
        if result.get('success'):
            logger.success("검수 완료")
            logger.info(f"검수된 공고: {result.get('reviewed_count', 0)}개")
            logger.info(f"적합: {result.get('approved_count', 0)}개")
            logger.info(f"부적합: {result.get('rejected_count', 0)}개")
        else:
            logger.error(f"검수 실패: {result.get('error', '알 수 없는 오류')}")
        
        return result
        
    except Exception as e:
        error_msg = f"검수 실패: {str(e)}"
        logger.error(error_msg)
        import traceback
        logger.error(traceback.format_exc())
        
        return {
            'success': False,
            'reviewed_count': 0,
            'approved_count': 0,
            'rejected_count': 0,
            'error': error_msg
        }
