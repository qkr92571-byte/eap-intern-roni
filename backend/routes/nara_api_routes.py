"""
나라장터 Open API 관련 라우트
낙찰정보 조회 및 경쟁사 동향 분석
"""

from flask import Blueprint, request
from services.nara_api_service import get_nara_api_service
from utils.response_helpers import (
    success_response,
    error_response,
    bad_request_response
)
from datetime import datetime, timedelta

nara_api_bp = Blueprint('nara_api', __name__)

@nara_api_bp.route('/award-info', methods=['GET'])
def get_award_info():
    """
    낙찰정보 조회
    
    Query Parameters:
        start_date: 시작일자 (YYYYMMDD 형식, 선택)
        end_date: 종료일자 (YYYYMMDD 형식, 선택)
        keyword: 검색 키워드 (선택)
        num_of_rows: 한 페이지 결과 수 (기본값: 100)
        page_no: 페이지 번호 (기본값: 1)
    """
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        keyword = request.args.get('keyword')
        num_of_rows = int(request.args.get('num_of_rows', 100))
        page_no = int(request.args.get('page_no', 1))
        
        service = get_nara_api_service()
        result = service.get_award_info(
            start_date=start_date,
            end_date=end_date,
            keyword=keyword,
            num_of_rows=num_of_rows,
            page_no=page_no
        )
        
        return success_response(data=result)
        
    except Exception as e:
        return error_response(str(e), 500)

@nara_api_bp.route('/award-info/keyword', methods=['GET'])
def get_award_info_by_keyword():
    """
    키워드로 낙찰정보 조회 (여러 페이지 자동 처리)
    
    Query Parameters:
        keyword: 검색 키워드 (필수)
        days: 조회할 일수 (기본값: 30)
    """
    try:
        keyword = request.args.get('keyword')
        if not keyword:
            return bad_request_response('keyword 파라미터가 필요합니다.')
        
        days = int(request.args.get('days', 30))
        
        service = get_nara_api_service()
        awards = service.get_award_info_by_keyword(keyword, days=days)
        
        return success_response(
            data={'awards': awards},
            count=len(awards)
        )
        
    except Exception as e:
        return error_response(str(e), 500)

@nara_api_bp.route('/competitor-analysis', methods=['GET', 'POST'])
def analyze_competitor_trends():
    """
    경쟁사 동향 분석
    
    GET: Query Parameters
        keywords: 콤마로 구분된 키워드 리스트 (예: "EAP,직원지원프로그램,상담")
        days: 분석 기간 일수 (기본값: 30)
    
    POST: Request Body
        {
            "keywords": ["EAP", "직원지원프로그램", "상담"],
            "days": 30
        }
    """
    try:
        if request.method == 'GET':
            keywords_str = request.args.get('keywords', '')
            if not keywords_str:
                return bad_request_response('keywords 파라미터가 필요합니다.')
            keywords = [k.strip() for k in keywords_str.split(',') if k.strip()]
            days = int(request.args.get('days', 30))
        else:
            data = request.get_json() or {}
            keywords = data.get('keywords', [])
            if not keywords:
                return bad_request_response('keywords 필드가 필요합니다.')
            days = int(data.get('days', 30))
        
        if not keywords:
            return bad_request_response('최소 1개 이상의 키워드가 필요합니다.')
        
        service = get_nara_api_service()
        analysis_result = service.analyze_competitor_trends(keywords, days=days)
        
        return success_response(data=analysis_result)
        
    except Exception as e:
        return error_response(str(e), 500)

