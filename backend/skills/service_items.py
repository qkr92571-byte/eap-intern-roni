"""
Skill: 적합 공고 첨부파일 조사 및 서비스 항목 수집

입력:
    - report_date: datetime (선택, 기본값: 오늘 KST)
    - confirm_policy: str ('interactive' 또는 'auto', 기본값: 'interactive')

출력:
    - result: Dict
        - success: bool
        - processed: int (처리 완료 개수)
        - skipped: int (건너뜀)
        - errors: int (오류)
        - error: str (실패 시)

부수 효과:
    - 파일 쓰기: backend/report/report_YYMMDD.json 업데이트 (service_items 필드 추가)
    - 파일 쓰기: 첨부파일 다운로드 (임시 디렉터리)
    - DB 쓰기: Firestore 업데이트 (service_items 반영)
"""

from datetime import datetime
from typing import Dict, Optional
import sys
import os

# 프로젝트 루트 경로 추가
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from scripts.process_approved_announcements import process_approved_announcements
from orchestration.policies import should_confirm, request_confirmation
from utils.logger import StepLogger


def skill_collect_service_items(
    report_date: Optional[datetime] = None,
    confirm_policy: str = 'interactive'
) -> Dict:
    """
    적합 판정 받은 공고들의 첨부파일 조사 및 서비스 항목 수집
    
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
    logger = StepLogger("스킬: 서비스 항목 수집")
    
    try:
        if report_date is None:
            # KST 기준 오늘 날짜
            from datetime import timezone, timedelta
            kst = timezone(timedelta(hours=9))
            report_date = datetime.now(kst)
        
        logger.info(f"날짜: {report_date.strftime('%Y-%m-%d')}")
        
        # 컨펌 정책 확인
        if should_confirm(confirm_policy):
            logger.warning("첨부파일 조사 및 서비스 항목 수집을 진행하시겠습니까?")
            logger.info("이 작업은 각 공고의 첨부파일을 다운로드하고 분석합니다.")
            
            if not request_confirmation("계속하려면 'yes' 또는 'y'를 입력하세요"):
                logger.warning("사용자가 첨부파일 조사를 건너뛰었습니다.")
                return {
                    'success': True,
                    'processed': 0,
                    'skipped': 0,
                    'errors': 0,
                    'error': '사용자가 건너뛰었습니다.'
                }
        
        logger.info("첨부파일 조사 시작...")
        
        # 기존 스크립트 함수 호출
        result = process_approved_announcements(report_date)
        
        # 반환값 형식 통일 (skipped, errors 필드 추가)
        if 'skipped' not in result:
            result['skipped'] = result.get('skipped_count', 0)
        if 'errors' not in result:
            result['errors'] = result.get('error_count', 0)
        
        if result.get('success'):
            logger.success("서비스 항목 수집 완료")
            logger.info(f"처리 완료: {result.get('processed', 0)}개")
            logger.info(f"건너뜀: {result.get('skipped', 0)}개")
            logger.info(f"오류: {result.get('errors', 0)}개")
        else:
            logger.warning(f"서비스 항목 수집 중 오류 발생: {result.get('error', '알 수 없는 오류')}")
        
        return result
        
    except Exception as e:
        error_msg = f"서비스 항목 수집 실패: {str(e)}"
        logger.error(error_msg)
        import traceback
        logger.error(traceback.format_exc())
        
        return {
            'success': False,
            'processed': 0,
            'skipped': 0,
            'errors': 0,
            'error': error_msg
        }
