"""
Report 및 History 관리 API 라우트
"""

from flask import Blueprint, request
from services.file_service import load_report, get_history_numbers
from services.firebase_service import save_announcement, init_firebase, check_duplicate_announcement
from services.review_service import review_report_file
from utils.response_helpers import (
    success_response,
    error_response,
    bad_request_response
)
from datetime import datetime

report_bp = Blueprint('reports', __name__)

@report_bp.route('/today', methods=['GET'])
def get_today_report():
    """오늘 수집된 report 조회"""
    try:
        report_data = load_report()
        return success_response(
            data={'announcements': report_data},
            count=len(report_data)
        )
    except Exception as e:
        return error_response(str(e), 500)

@report_bp.route('/upload', methods=['POST'])
def upload_to_firestore():
    """
    수집된 데이터를 Firestore에 업로드 (사용자 컨펌 후)
    
    Request Body:
    {
        "date": "241130"  # 선택사항, 없으면 오늘
    }
    """
    try:
        data = request.get_json() or {}
        date_str = data.get('date')
        
        # 날짜 파싱
        if date_str:
            try:
                report_date = datetime.strptime(date_str, '%y%m%d')
            except:
                return bad_request_response('날짜 형식이 올바르지 않습니다 (YYMMDD 형식)')
        else:
            report_date = datetime.now()
        
        # Report 파일에서 데이터 로드
        report_data = load_report(report_date)
        
        if not report_data:
            return success_response(
                data={'announcements': []},
                message='업로드할 데이터가 없습니다',
                count=0
            )
        
        # Firestore에 저장
        uploaded_count = 0
        failed_count = 0
        
        for announcement in report_data:
            try:
                # 중복 체크 (Firestore 기준)
                announcement_number = announcement.get('announcement_number', '')
                if announcement_number:
                    from services.firebase_service import check_duplicate_announcement
                    if check_duplicate_announcement(announcement_number):
                        failed_count += 1
                        continue
                
                # 저장
                save_announcement(announcement)
                uploaded_count += 1
            except Exception as e:
                print(f"공고 업로드 실패: {str(e)}")
                failed_count += 1
                continue
        
        return success_response(
            data={'announcements': report_data[:uploaded_count]},
            message=f'{uploaded_count}개의 공고를 Firestore에 업로드했습니다 (실패: {failed_count}개)',
            count=uploaded_count
        )
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return error_response(str(e), 500)

@report_bp.route('/review', methods=['POST'])
def review_report():
    """
    리포트 파일을 ChatGPT API로 검수
    
    Request Body:
    {
        "date": "241130",  # 선택사항, 없으면 오늘
        "skip_confirmation": false  # 선택사항, true면 컨펌 없이 실행 (기본값: false)
    }
    
    ⚠️  ChatGPT API 사용 시 비용이 발생합니다. skip_confirmation을 true로 설정하지 않으면 컨펌이 필요합니다.
    """
    try:
        data = request.get_json() or {}
        date_str = data.get('date')
        skip_confirmation = data.get('skip_confirmation', False)
        
        # 날짜 파싱
        if date_str:
            try:
                report_date = datetime.strptime(date_str, '%y%m%d')
            except:
                return bad_request_response('날짜 형식이 올바르지 않습니다 (YYMMDD 형식)')
        else:
            report_date = datetime.now()
        
        # 리포트 파일 검수 (API에서는 skip_confirmation이 True일 때만 컨펌 없이 실행)
        review_result = review_report_file(report_date, confirm_before_review=not skip_confirmation)
        
        if not review_result.get('success', False):
            return error_response(
                review_result.get('error', '검수 중 오류가 발생했습니다'),
                500
            )
        
        return success_response(
            data={
                'reviewed_count': review_result.get('reviewed_count', 0),
                'approved_count': review_result.get('approved_count', 0),
                'rejected_count': review_result.get('rejected_count', 0),
                'report_path': review_result.get('report_path', '')
            },
            message='리포트 검수가 완료되었습니다',
            count=review_result.get('reviewed_count', 0)
        )
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return error_response(str(e), 500)

@report_bp.route('/review-and-upload', methods=['POST'])
def review_and_upload():
    """
    리포트 파일 검수 및 Firestore 업로드 통합
    
    Request Body:
    {
        "date": "241130",  # 선택사항, 없으면 오늘
        "upload_approved_only": false,  # 선택사항, 승인된 공고만 업로드 (기본값: false, 부적합도 포함)
        "skip_confirmation": false  # 선택사항, true면 컨펌 없이 실행 (기본값: false)
    }
    
    ⚠️  ChatGPT API 사용 시 비용이 발생합니다. skip_confirmation을 true로 설정하지 않으면 컨펌이 필요합니다.
    """
    try:
        data = request.get_json() or {}
        date_str = data.get('date')
        upload_approved_only = data.get('upload_approved_only', False)  # 기본값: False (부적합도 포함)
        skip_confirmation = data.get('skip_confirmation', False)
        
        # 날짜 파싱
        if date_str:
            try:
                report_date = datetime.strptime(date_str, '%y%m%d')
            except:
                return bad_request_response('날짜 형식이 올바르지 않습니다 (YYMMDD 형식)')
        else:
            report_date = datetime.now()
        
        # 1단계: 리포트 파일 검수 (API에서는 skip_confirmation이 True일 때만 컨펌 없이 실행)
        review_result = review_report_file(report_date, confirm_before_review=not skip_confirmation)
        
        if not review_result.get('success', False):
            return error_response(
                review_result.get('error', '검수 중 오류가 발생했습니다'),
                500
            )
        
        # 2단계: Firebase 초기화
        try:
            init_firebase()
        except Exception as e:
            return error_response(f'Firebase 초기화 실패: {str(e)}', 500)
        
        # 3단계: Firestore 업로드
        report_data = load_report(report_date)
        
        if not report_data:
            return success_response(
                data={'announcements': []},
                message='업로드할 데이터가 없습니다',
                count=0
            )
        
        # 업로드할 공고 필터링
        if upload_approved_only:
            upload_announcements = [
                a for a in report_data 
                if a.get('status') == 'approved'
            ]
        else:
            upload_announcements = report_data
        
        uploaded_count = 0
        skipped_count = 0
        failed_count = 0
        
        for announcement in upload_announcements:
            try:
                announcement_number = announcement.get('announcement_number', '')
                
                if not announcement_number:
                    skipped_count += 1
                    continue
                
                # 중복 체크
                if check_duplicate_announcement(announcement_number):
                    skipped_count += 1
                    continue
                
                # Firestore 스키마에 맞게 데이터 변환
                firestore_data = {
                    'title': announcement.get('title', ''),
                    'announcement_number': announcement_number,
                    'agency': announcement.get('agency', ''),
                    'publish_date': announcement.get('publish_date', ''),
                    'budget_amount': announcement.get('budget_amount'),
                    'estimated_price': announcement.get('estimated_price'),
                    'business_type': announcement.get('business_type', ''),
                    'created_at': announcement.get('created_at', datetime.now().isoformat()),
                    'source': announcement.get('source', '나라장터'),
                    'status': announcement.get('status', 'pending'),
                    'filtered': announcement.get('filtered', False),
                    'reviewed': announcement.get('reviewed', True),
                    'review_result': announcement.get('review_result', ''),
                    'review_model': announcement.get('review_model', ''),
                    'reviewed_at': announcement.get('reviewed_at', '')
                }
                
                # None 값 제거
                firestore_data = {k: v for k, v in firestore_data.items() if v is not None}
                
                # 저장
                save_announcement(firestore_data)
                uploaded_count += 1
                
            except Exception as e:
                print(f"공고 업로드 실패: {str(e)}")
                failed_count += 1
                continue
        
        return success_response(
            data={
                'reviewed_count': review_result.get('reviewed_count', 0),
                'approved_count': review_result.get('approved_count', 0),
                'rejected_count': review_result.get('rejected_count', 0),
                'uploaded_count': uploaded_count,
                'skipped_count': skipped_count,
                'failed_count': failed_count
            },
            message=f'검수 및 업로드가 완료되었습니다 (검수: {review_result.get("reviewed_count", 0)}개, 업로드: {uploaded_count}개)',
            count=uploaded_count
        )
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return error_response(str(e), 500)


