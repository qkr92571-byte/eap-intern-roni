"""
Report 및 History 관리 API 라우트
"""

from flask import Blueprint, request
from services.file_service import load_report, get_history_numbers
from services.firebase_service import save_announcement
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


