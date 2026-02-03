"""
Skill: 나라장터(G2B) 공고 수집

입력:
    - keywords: List[str] (선택, 없으면 Firestore에서 조회)
    - request_date: datetime (선택, 기본값: 오늘 KST)

출력:
    - result: Dict
        - success: bool
        - report_file_path: str (생성된 리포트 파일 경로)
        - collected_count: int (수집된 공고 개수)
        - error: str (실패 시)

부수 효과:
    - 파일 쓰기: backend/report/report_YYMMDD.json 생성/업데이트
    - 파일 쓰기: backend/history/history_YYMMDD.json 생성/업데이트
"""

from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

from services.scraper_service import run_scraper
from services.file_service import REPORT_DIR, get_date_string
from utils.logger import StepLogger


def skill_scrape_g2b(
    keywords: Optional[List[str]] = None,
    request_date: Optional[datetime] = None
) -> Dict:
    """
    나라장터(G2B)에서 키워드 기반 공고 수집
    
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
    logger = StepLogger("스킬: 나라장터 공고 수집")
    
    try:
        if request_date is None:
            # KST 기준 오늘 날짜 (플랜에 따라 명시적 KST 사용)
            from datetime import timezone, timedelta
            kst = timezone(timedelta(hours=9))
            request_date = datetime.now(kst)
        
        logger.info(f"날짜: {request_date.strftime('%Y-%m-%d')}")
        logger.info(f"키워드: {keywords if keywords else 'Firestore에서 조회'}")
        
        # 기존 서비스 호출
        results = run_scraper(keywords=keywords, request_date=request_date)
        
        # 리포트 파일 경로 생성
        date_str = get_date_string(request_date)
        report_file_path = str(REPORT_DIR / f'report_{date_str}.json')
        
        collected_count = len(results) if results else 0
        
        logger.success(f"수집 완료: {collected_count}개 공고")
        logger.info(f"리포트 파일: {report_file_path}")
        
        return {
            'success': True,
            'report_file_path': report_file_path,
            'collected_count': collected_count,
            'error': None
        }
        
    except Exception as e:
        error_msg = f"공고 수집 실패: {str(e)}"
        logger.error(error_msg)
        import traceback
        logger.error(traceback.format_exc())
        
        return {
            'success': False,
            'report_file_path': None,
            'collected_count': 0,
            'error': error_msg
        }
