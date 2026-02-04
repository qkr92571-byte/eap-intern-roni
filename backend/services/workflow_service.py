"""
워크플로우 서비스 (레거시)

⚠️ DEPRECATED:
- 이 모듈은 멀티 에이전트 + Orchestrator 기반 워크플로우 도입 이전의 코드입니다.
- 신규/운영 워크플로우 구현 시에는 `backend/entrypoints/daily_report.py`와
  Orchestrator/Agents/Skills 구조를 사용하세요.
- 이 모듈은 기존 스크립트(`scripts/review_and_upload_report.py`) 호환 및
  디버깅 목적에서만 유지됩니다.
"""

from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

from services.review_service import review_report_file
from services.file_service import load_report, REPORT_DIR, get_date_string
from services.firebase_service import init_firebase, save_announcement, check_duplicate_announcement
from services.slack_service import send_report_to_slack
from scripts.process_approved_announcements import process_approved_announcements
from utils.constants import STATUS_APPROVED, STATUS_REJECTED, SLACK_PRODUCTION_CHANNEL_ID
from utils.logger import StepLogger
from orchestration.policies import request_confirmation


class WorkflowService:
    """리포트 검수 및 업로드 워크플로우 서비스"""
    
    def __init__(self, report_date: Optional[datetime] = None, auto_upload: bool = False):
        """
        Args:
            report_date: 리포트 날짜 (기본값: 오늘)
            auto_upload: 자동 업로드 모드 (사용자 입력 없이 진행)
        """
        self.report_date = report_date or datetime.now()
        self.auto_upload = auto_upload
        self.logger = StepLogger("리포트 검수 및 Firestore 업로드")
    
    def run_review_step(self, confirm_before_review: bool = False) -> Dict:
        """
        1단계: 리포트 파일 검수
        
        Args:
            confirm_before_review: 검수 전 사용자 컨펌 받기
            
        Returns:
            검수 결과 딕셔너리
        """
        self.logger.start()
        self.logger.info(f"날짜: {self.report_date.strftime('%Y-%m-%d')}")
        self.logger.section("[1단계] 리포트 파일 검수")
        
        review_result = review_report_file(
            self.report_date,
            confirm_before_review=confirm_before_review
        )
        
        if not review_result.get('success', False):
            self.logger.error(f"검수 실패: {review_result.get('error', '알 수 없는 오류')}")
            return review_result
        
        self.logger.success("검수 완료!")
        self.logger.info(f"검수된 공고: {review_result.get('reviewed_count', 0)}개")
        self.logger.info(f"승인: {review_result.get('approved_count', 0)}개")
        self.logger.info(f"거부: {review_result.get('rejected_count', 0)}개")
        
        return review_result
    
    def run_service_items_step(self, review_result: Dict) -> Dict:
        """
        2단계: 적합 판정 받은 공고들의 첨부파일 조사 및 서비스 항목 수집
        
        Args:
            review_result: 검수 결과 딕셔너리
            
        Returns:
            서비스 항목 수집 결과 딕셔너리
        """
        approved_count = review_result.get('approved_count', 0)
        
        self.logger.section("[2단계] 적합 판정 공고 첨부파일 조사 및 서비스 항목 수집")
        
        if approved_count == 0:
            self.logger.warning("적합 판정 받은 공고가 없어 첨부파일 조사를 건너뜁니다.")
            return {
                'success': True,
                'processed': 0,
                'skipped': 0,
                'errors': 0,
                'message': '적합 판정 받은 공고가 없습니다.'
            }
        
        self.logger.info(f"적합 판정 받은 공고 {approved_count}개에 대해 첨부파일 조사를 진행합니다.")
        
        # 사용자 컨펌 요청
        if self.auto_upload:
            self.logger.success("자동 모드: 첨부파일 조사를 진행합니다...")
            process_service_items = True
        else:
            self.logger.warning("첨부파일 조사 및 서비스 항목 수집을 진행하시겠습니까?")
            self.logger.info("이 작업은 각 공고의 첨부파일을 다운로드하고 분석합니다.")
            process_service_items = request_confirmation("계속하려면 'yes' 또는 'y'를 입력하세요: ")
        
        if not process_service_items:
            self.logger.warning("사용자가 첨부파일 조사를 건너뛰었습니다.")
            return {
                'success': True,
                'processed': 0,
                'skipped': approved_count,
                'errors': 0,
                'message': '사용자가 건너뛰었습니다.'
            }
        
        self.logger.success("사용자 컨펌 확인됨. 첨부파일 조사를 시작합니다...")
        service_result = process_approved_announcements(self.report_date)
        
        if service_result.get('success'):
            self.logger.success("서비스 항목 수집 완료!")
            self.logger.info(f"처리 완료: {service_result.get('processed', 0)}개")
            self.logger.info(f"건너뜀: {service_result.get('skipped', 0)}개")
            self.logger.info(f"오류: {service_result.get('errors', 0)}개")
        else:
            self.logger.warning(f"서비스 항목 수집 중 오류 발생: {service_result.get('error', '알 수 없는 오류')}")
        
        return service_result
    
    def run_firestore_upload_step(self) -> Dict:
        """
        3단계: Firebase 초기화 및 Firestore 업로드
        
        Returns:
            업로드 결과 딕셔너리
        """
        # Firebase 초기화
        self.logger.section("[3단계] Firebase 초기화")
        try:
            init_firebase()
            self.logger.success("Firebase 초기화 성공")
        except Exception as e:
            self.logger.error(f"Firebase 초기화 실패: {str(e)}")
            self.logger.info("Firebase 키 파일을 확인해주세요.")
            return {
                'success': False,
                'error': f'Firebase 초기화 실패: {str(e)}',
                'uploaded': 0,
                'skipped': 0,
                'failed': 0
            }
        
        # Firestore 업로드
        self.logger.section("[4단계] Firestore 업로드")
        
        report_data = load_report(self.report_date)
        if not report_data:
            self.logger.warning("업로드할 데이터가 없습니다.")
            return {
                'success': False,
                'error': '업로드할 데이터가 없습니다.',
                'uploaded': 0,
                'skipped': 0,
                'failed': 0
            }
        
        approved_count = len([a for a in report_data if a.get('status') == STATUS_APPROVED])
        rejected_count = len([a for a in report_data if a.get('status') == STATUS_REJECTED])
        
        self.logger.info(f"업로드할 공고: {len(report_data)}개")
        self.logger.info(f"  - 적합 공고: {approved_count}개")
        self.logger.info(f"  - 부적합 공고: {rejected_count}개")
        self.logger.info(f"  - 전체 업로드: {len(report_data)}개 (적합/부적합 모두 포함)")
        
        # 사용자 컨펌 요청
        if self.auto_upload:
            self.logger.success("자동 업로드 모드: Firestore 업로드를 진행합니다...")
        else:
            self.logger.warning("Firestore 업로드를 진행하시겠습니까?")
            self.logger.info("이 작업은 데이터베이스에 데이터를 저장합니다.")
            if not request_confirmation("계속하려면 'yes' 또는 'y'를 입력하세요: "):
                self.logger.warning("사용자가 업로드를 취소했습니다.")
                self.logger.info("Firestore 업로드를 건너뜁니다.")
                return {
                    'success': True,
                    'uploaded': 0,
                    'skipped': 0,
                    'failed': 0,
                    'message': '사용자가 취소했습니다.'
                }
        
        self.logger.success("사용자 컨펌 확인됨. Firestore 업로드를 시작합니다...")
        
        uploaded_count = 0
        skipped_count = 0
        failed_count = 0
        
        for idx, announcement in enumerate(report_data, 1):
            try:
                announcement_number = announcement.get('announcement_number', '')
                
                if not announcement_number:
                    self.logger.warning(f"[{idx}/{len(report_data)}] 공고번호가 없어 건너뜀")
                    skipped_count += 1
                    continue
                
                # 중복 체크
                if check_duplicate_announcement(announcement_number):
                    self.logger.info(f"[{idx}/{len(report_data)}] 중복 공고 건너뜀: {announcement_number}")
                    skipped_count += 1
                    continue
                
                # 상태 확인
                status = announcement.get('status', 'pending')
                status_icon = "✅" if status == STATUS_APPROVED else "❌" if status == STATUS_REJECTED else "⏳"
                
                # Firestore 스키마에 맞게 데이터 변환
                firestore_data = self._prepare_firestore_data(announcement)
                
                # 저장
                doc_id = save_announcement(firestore_data)
                uploaded_count += 1
                
                if idx % 10 == 0:
                    self.logger.info(f"진행 중... {idx}/{len(report_data)} (업로드: {uploaded_count}, 건너뜀: {skipped_count})")
                else:
                    self.logger.info(f"[{idx}/{len(report_data)}] {status_icon} 업로드 ({status}): {announcement_number}")
                
            except Exception as e:
                self.logger.error(f"[{idx}/{len(report_data)}] 업로드 실패: {str(e)}")
                failed_count += 1
                continue
        
        return {
            'success': True,
            'uploaded': uploaded_count,
            'skipped': skipped_count,
            'failed': failed_count,
            'total': len(report_data)
        }
    
    def run_slack_notification_step(self, skip_slack: bool = False) -> bool:
        """
        5단계: 슬랙 메시지 전송
        
        Args:
            skip_slack: 슬랙 전송 건너뛰기 여부
            
        Returns:
            전송 성공 여부
        """
        self.logger.section("[5단계] 슬랙 메시지 전송")
        
        if skip_slack:
            self.logger.warning("슬랙 전송이 건너뛰어졌습니다.")
            return False
        
        report_file = REPORT_DIR / f'report_{get_date_string(self.report_date)}.json'
        if not report_file.exists():
            self.logger.warning("리포트 파일을 찾을 수 없어 슬랙 전송을 건너뜁니다.")
            return False
        
        # 사용자 컨펌 요청 (공식 채널 전송)
        self.logger.warning("공식 채널로 슬랙 메시지를 전송하시겠습니까?")
        self.logger.info(f"공식 채널: {SLACK_PRODUCTION_CHANNEL_ID}")
        self.logger.info("이 작업은 공식 슬랙 채널에 리포트 메시지를 전송합니다.")
        
        if not self.auto_upload:
            if not request_confirmation("계속하려면 'yes' 또는 'y'를 입력하세요: "):
                self.logger.warning("사용자가 공식 채널 전송을 취소했습니다.")
                return False
        
        self.logger.success("사용자 컨펌 확인됨. 공식 채널로 전송을 시작합니다...")
        self.logger.info(f"공식 채널: {SLACK_PRODUCTION_CHANNEL_ID}")
        
        success = send_report_to_slack(str(report_file), channel_id=SLACK_PRODUCTION_CHANNEL_ID)
        if success:
            self.logger.success("공식 채널 슬랙 메시지 전송 완료")
        else:
            self.logger.warning("공식 채널 슬랙 메시지 전송 실패 (환경변수 확인 필요)")
        
        return success
    
    def _prepare_firestore_data(self, announcement: Dict) -> Dict:
        """
        공고 데이터를 Firestore 스키마에 맞게 변환
        
        Args:
            announcement: 공고 데이터 딕셔너리
            
        Returns:
            Firestore에 저장할 데이터 딕셔너리
        """
        firestore_data = {
            'title': announcement.get('title', ''),
            'announcement_number': announcement.get('announcement_number', ''),
            'agency': announcement.get('agency', ''),
            'publish_date': announcement.get('publish_date', ''),
            'budget_amount': announcement.get('budget_amount'),
            'estimated_price': announcement.get('estimated_price'),
            'business_type': announcement.get('business_type', ''),
            'created_at': announcement.get('created_at', datetime.now().isoformat()),
            'source': announcement.get('source', '나라장터'),
            'status': announcement.get('status', STATUS_APPROVED),
            'filtered': announcement.get('filtered', False),
            'reviewed': announcement.get('reviewed', True),
            'review_result': announcement.get('review_result', ''),
            'review_model': announcement.get('review_model', ''),
            'reviewed_at': announcement.get('reviewed_at', ''),
            'service_items': announcement.get('service_items'),
            'service_items_extracted_at': announcement.get('service_items_extracted_at'),
            'display_status': announcement.get('display_status', 20)  # 20: 노출, 40: 삭제됨
        }
        
        # None 값 제거
        return {k: v for k, v in firestore_data.items() if v is not None}
    
    def run_full_workflow(self, skip_slack: bool = False, confirm_before_review: bool = False) -> Dict:
        """
        전체 워크플로우 실행
        
        Args:
            skip_slack: 슬랙 전송 건너뛰기 여부
            confirm_before_review: 검수 전 사용자 컨펌 받기
            
        Returns:
            전체 워크플로우 결과 딕셔너리
        """
        try:
            # 1단계: 리포트 검수
            review_result = self.run_review_step(confirm_before_review=confirm_before_review)
            if not review_result.get('success'):
                return {
                    'success': False,
                    'error': review_result.get('error', '검수 실패'),
                    'review_result': review_result
                }
            
            # 2단계: 서비스 항목 수집
            service_result = self.run_service_items_step(review_result)
            
            # 3단계: Firestore 업로드
            upload_result = self.run_firestore_upload_step()
            if not upload_result.get('success'):
                return {
                    'success': False,
                    'error': upload_result.get('error', '업로드 실패'),
                    'review_result': review_result,
                    'service_result': service_result,
                    'upload_result': upload_result
                }
            
            # 4단계: 슬랙 전송
            slack_sent = self.run_slack_notification_step(skip_slack=skip_slack)
            
            # 최종 결과 출력
            self.logger.section("전체 프로세스 완료!")
            self.logger.info("[검수 결과]")
            self.logger.info(f"  검수된 공고: {review_result.get('reviewed_count', 0)}개")
            self.logger.info(f"  적합: {review_result.get('approved_count', 0)}개")
            self.logger.info(f"  부적합: {review_result.get('rejected_count', 0)}개")
            self.logger.info("[업로드 결과]")
            self.logger.info(f"  전체 공고: {upload_result.get('total', 0)}개 (적합/부적합 모두 포함)")
            self.logger.info(f"  업로드 성공: {upload_result.get('uploaded', 0)}개")
            self.logger.info(f"  건너뜀 (중복): {upload_result.get('skipped', 0)}개")
            self.logger.info(f"  실패: {upload_result.get('failed', 0)}개")
            
            return {
                'success': True,
                'review_result': review_result,
                'service_result': service_result,
                'upload_result': upload_result,
                'slack_sent': slack_sent
            }
            
        except Exception as e:
            self.logger.error(f"오류 발생: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return {
                'success': False,
                'error': str(e)
            }

