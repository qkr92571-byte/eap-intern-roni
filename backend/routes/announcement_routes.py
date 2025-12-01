from flask import Blueprint, request
from services.firebase_service import (
    get_announcements,
    get_announcement_by_id,
    save_announcement,
    update_announcement,
    delete_announcement
)
from services.scraper_service import run_scraper
from services.filter_service import filter_announcements
from utils.response_helpers import (
    success_response,
    error_response,
    not_found_response,
    bad_request_response
)
from utils.constants import DEFAULT_LIMIT, MAX_LIMIT

announcement_bp = Blueprint('announcements', __name__)

@announcement_bp.route('', methods=['GET'])
def list_announcements():
    """공고 목록 조회"""
    try:
        filters = {}
        
        # 쿼리 파라미터로 필터링
        status = request.args.get('status')
        if status:
            filters['status'] = status
        
        try:
            limit = int(request.args.get('limit', DEFAULT_LIMIT))
            limit = min(limit, MAX_LIMIT)  # 최대값 제한
        except ValueError:
            limit = DEFAULT_LIMIT
        
        announcements = get_announcements(filters=filters, limit=limit)
        return success_response(
            data=announcements,
            count=len(announcements)
        )
    except Exception as e:
        return error_response(str(e), 500)

@announcement_bp.route('/<announcement_id>', methods=['GET'])
def get_announcement(announcement_id):
    """특정 공고 조회"""
    try:
        announcement = get_announcement_by_id(announcement_id)
        if announcement:
            return success_response(data=announcement)
        return not_found_response('공고를 찾을 수 없습니다')
    except Exception as e:
        return error_response(str(e), 500)

@announcement_bp.route('', methods=['POST'])
def create_announcement():
    """공고 수동 생성 (테스트용)"""
    try:
        data = request.get_json()
        if not data:
            return bad_request_response('요청 데이터가 없습니다')
        
        announcement_id = save_announcement(data)
        return success_response(data={'id': announcement_id}, message='공고가 생성되었습니다'), 201
    except Exception as e:
        return error_response(str(e), 500)

@announcement_bp.route('/<announcement_id>', methods=['PUT'])
def update_announcement_route(announcement_id):
    """공고 업데이트"""
    try:
        data = request.get_json()
        if not data:
            return bad_request_response('업데이트할 데이터가 없습니다')
        
        update_announcement(announcement_id, data)
        return success_response(message='공고가 업데이트되었습니다')
    except Exception as e:
        return error_response(str(e), 500)

@announcement_bp.route('/<announcement_id>', methods=['DELETE'])
def delete_announcement_route(announcement_id):
    """공고 삭제"""
    try:
        delete_announcement(announcement_id)
        return success_response(message='공고가 삭제되었습니다')
    except Exception as e:
        return error_response(str(e), 500)

@announcement_bp.route('/scrape', methods=['POST'])
def scrape_announcements():
    """
    나라장터 공고 수집 실행 (수동 실행)
    
    Request Body:
    {
        "keywords": ["키워드1", "키워드2"]  # 선택사항, 없으면 전체 공고 수집
    }
    """
    try:
        data = request.get_json() or {}
        keywords = data.get('keywords', [])
        
        # 키워드가 문자열 리스트인지 확인
        if not isinstance(keywords, list):
            keywords = []
        
        print(f"스크래퍼 실행 시작 - 키워드: {keywords}")
        
        # 스크래퍼 실행 (로컬 파일 저장)
        from datetime import datetime
        results = run_scraper(keywords=keywords, request_date=datetime.now())
        
        keyword_info = f' (키워드: {", ".join(keywords)})' if keywords else ' (전체 공고)'
        
        print(f"스크래퍼 실행 완료 - 수집된 공고: {len(results)}개")
        
        return success_response(
            data=results,
            message=f'{len(results)}개의 공고를 수집했습니다{keyword_info}',
            count=len(results)
        )
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"스크래퍼 실행 중 오류 발생: {str(e)}")
        print(f"상세 오류:\n{error_trace}")
        return error_response(f'수집 중 오류 발생: {str(e)}', 500)

@announcement_bp.route('/filter', methods=['POST'])
def filter_announcements_route():
    """공고 필터링 및 검수"""
    try:
        data = request.get_json()
        if not data:
            return bad_request_response('요청 데이터가 없습니다')
        
        announcement_ids = data.get('announcement_ids', [])
        keywords = data.get('keywords', [])
        
        if not announcement_ids:
            return bad_request_response('공고 ID 목록이 필요합니다')
        
        results = filter_announcements(announcement_ids, keywords)
        
        return success_response(
            data=results,
            message=f'{len(results)}개의 공고를 검수했습니다',
            count=len(results)
        )
    except Exception as e:
        return error_response(str(e), 500)
