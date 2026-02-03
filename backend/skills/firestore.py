"""
Skill: Firestore 업로드(Upsert)

입력:
    - report_date: datetime (선택, 기본값: 오늘 KST)
    - report_data: List[Dict] (선택, report_date가 없을 때 사용)
    - confirm_policy: str ('interactive' 또는 'auto', 기본값: 'interactive')

출력:
    - result: Dict
        - success: bool
        - uploaded: int (추가된 개수)
        - updated: int (업데이트된 개수)
        - skipped: int (건너뜀)
        - failed: int (실패)
        - error: str (실패 시)

부수 효과:
    - DB 쓰기: Firestore 'announcements' 컬렉션에 데이터 추가/업데이트
    - 컨펌 정책에 따라 사용자 확인 필요할 수 있음
"""

from datetime import datetime
from typing import List, Dict, Optional

from services.file_service import load_report
from services.firebase_service import (
    init_firebase,
    get_db,
    save_announcement,
    update_announcement,
)
from orchestration.policies import should_confirm, request_confirmation
from utils.logger import StepLogger


def _prepare_firestore_data(announcement: Dict) -> Dict:
    """Firestore 스키마에 맞게 공고 데이터 정리 (None 제거)"""
    firestore_data = {
        "title": announcement.get("title", ""),
        "announcement_number": announcement.get("announcement_number", ""),
        "agency": announcement.get("agency", ""),
        "publish_date": announcement.get("publish_date", ""),
        "budget_amount": announcement.get("budget_amount"),
        "estimated_price": announcement.get("estimated_price"),
        "business_type": announcement.get("business_type", ""),
        "created_at": announcement.get("created_at", datetime.now().isoformat()),
        "source": announcement.get("source", "나라장터"),
        "status": announcement.get("status", "pending"),
        "filtered": announcement.get("filtered", False),
        "reviewed": announcement.get("reviewed", True),
        "review_result": announcement.get("review_result", ""),
        "review_model": announcement.get("review_model", ""),
        "reviewed_at": announcement.get("reviewed_at", ""),
        "service_items": announcement.get("service_items"),
        "service_items_extracted_at": announcement.get("service_items_extracted_at"),
        "display_status": announcement.get("display_status", 20),  # 20: 노출, 40: 삭제됨
    }
    
    return {k: v for k, v in firestore_data.items() if v is not None}


def skill_upsert_firestore(
    report_date: Optional[datetime] = None,
    report_data: Optional[List[Dict]] = None,
    confirm_policy: str = 'interactive'
) -> Dict:
    """
    리포트 데이터를 Firestore에 업로드(Upsert)
    
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
    logger = StepLogger("스킬: Firestore 업로드")
    
    try:
        # 리포트 데이터 로드
        if report_data is None:
            if report_date is None:
                # KST 기준 오늘 날짜
                from datetime import timezone, timedelta
                kst = timezone(timedelta(hours=9))
                report_date = datetime.now(kst)
            
            logger.info(f"날짜: {report_date.strftime('%Y-%m-%d')}")
            report_data = load_report(report_date)
        
        if not report_data or not isinstance(report_data, list):
            error_msg = "업로드할 데이터가 없습니다."
            logger.warning(error_msg)
            return {
                'success': False,
                'uploaded': 0,
                'updated': 0,
                'skipped': 0,
                'failed': 0,
                'error': error_msg
            }
        
        # 컨펌 정책 확인
        if should_confirm(confirm_policy):
            approved_count = len([a for a in report_data if a.get('status') == 'approved'])
            rejected_count = len([a for a in report_data if a.get('status') == 'rejected'])
            
            logger.warning("Firestore 업로드를 진행하시겠습니까?")
            logger.info(f"업로드할 공고: {len(report_data)}개")
            logger.info(f"  - 적합 공고: {approved_count}개")
            logger.info(f"  - 부적합 공고: {rejected_count}개")
            logger.info("이 작업은 데이터베이스에 데이터를 저장합니다.")
            
            if not request_confirmation("계속하려면 'yes' 또는 'y'를 입력하세요"):
                logger.warning("사용자가 업로드를 취소했습니다.")
                return {
                    'success': True,
                    'uploaded': 0,
                    'updated': 0,
                    'skipped': 0,
                    'failed': 0,
                    'error': '사용자가 취소했습니다.'
                }
        
        # Firebase 초기화
        logger.info("Firebase 초기화 중...")
        init_firebase()
        db = get_db()
        logger.success("Firebase 초기화 완료")
        
        # 공고번호 기준으로 기존 문서들을 한 번에 조회(쿼리 최소화)
        numbers = []
        for ann in report_data:
            num = (ann.get("announcement_number") or "").strip()
            if num:
                numbers.append(num)
        
        existing_by_number: Dict[str, str] = {}
        chunk_size = 30  # Firestore 'in' 쿼리 제한
        for i in range(0, len(numbers), chunk_size):
            chunk = numbers[i : i + chunk_size]
            if not chunk:
                continue
            docs = db.collection("announcements").where("announcement_number", "in", chunk).stream()
            for doc in docs:
                data = doc.to_dict() or {}
                num = (data.get("announcement_number") or "").strip()
                if num:
                    existing_by_number[num] = doc.id
        
        uploaded = 0  # 추가
        updated = 0   # 업데이트
        skipped = 0
        failed = 0
        
        logger.info(f"업로드 시작: {len(report_data)}개 공고")
        
        for idx, ann in enumerate(report_data, 1):
            try:
                announcement_number = (ann.get("announcement_number") or "").strip()
                if not announcement_number:
                    skipped += 1
                    continue
                
                firestore_data = _prepare_firestore_data(ann)
                
                doc_id = existing_by_number.get(announcement_number)
                if doc_id:
                    update_announcement(doc_id, firestore_data)
                    updated += 1
                else:
                    save_announcement(firestore_data)
                    uploaded += 1
                
                if idx % 10 == 0:
                    logger.info(f"진행 중... {idx}/{len(report_data)} (추가 {uploaded}, 업데이트 {updated}, 건너뜀 {skipped}, 실패 {failed})")
                    
            except Exception as e:
                failed += 1
                logger.error(f"업로드 실패: {announcement_number} - {e}")
        
        logger.success("업로드 완료")
        logger.info(f"추가: {uploaded}개, 업데이트: {updated}개, 건너뜀: {skipped}개, 실패: {failed}개")
        
        return {
            'success': True,
            'uploaded': uploaded,
            'updated': updated,
            'skipped': skipped,
            'failed': failed,
            'error': None
        }
        
    except Exception as e:
        error_msg = f"Firestore 업로드 실패: {str(e)}"
        logger.error(error_msg)
        import traceback
        logger.error(traceback.format_exc())
        
        return {
            'success': False,
            'uploaded': 0,
            'updated': 0,
            'skipped': 0,
            'failed': 0,
            'error': error_msg
        }
