"""
키워드 관리 API 라우트
"""

from flask import Blueprint, request
from services.keyword_service import (
    get_keywords,
    add_keyword,
    remove_keyword,
    set_keywords
)
from utils.response_helpers import (
    success_response,
    error_response,
    bad_request_response
)

keyword_bp = Blueprint('keywords', __name__)

@keyword_bp.route('', methods=['GET'])
def list_keywords():
    """키워드 목록 조회"""
    try:
        keywords = get_keywords()
        return success_response(
            data={'keywords': keywords},
            count=len(keywords)
        )
    except Exception as e:
        return error_response(str(e), 500)

@keyword_bp.route('', methods=['POST'])
def create_keyword():
    """키워드 추가"""
    try:
        data = request.get_json()
        if not data:
            return bad_request_response('요청 데이터가 없습니다')
        
        keyword = data.get('keyword', '').strip()
        if not keyword:
            return bad_request_response('키워드를 입력해주세요')
        
        if add_keyword(keyword):
            keywords = get_keywords()
            return success_response(
                data={'keywords': keywords},
                message=f'키워드 "{keyword}"가 추가되었습니다',
                count=len(keywords)
            )
        else:
            return error_response('키워드 추가 실패', 500)
    except Exception as e:
        return error_response(str(e), 500)

@keyword_bp.route('/<keyword>', methods=['DELETE'])
def delete_keyword(keyword):
    """키워드 삭제"""
    try:
        if not keyword:
            return bad_request_response('키워드를 입력해주세요')
        
        if remove_keyword(keyword):
            keywords = get_keywords()
            return success_response(
                data={'keywords': keywords},
                message=f'키워드 "{keyword}"가 삭제되었습니다',
                count=len(keywords)
            )
        else:
            return error_response('키워드 삭제 실패', 500)
    except Exception as e:
        return error_response(str(e), 500)

@keyword_bp.route('', methods=['PUT'])
def update_keywords():
    """키워드 목록 전체 업데이트"""
    try:
        data = request.get_json()
        if not data:
            return bad_request_response('요청 데이터가 없습니다')
        
        keywords = data.get('keywords', [])
        if not isinstance(keywords, list):
            return bad_request_response('키워드는 배열 형식이어야 합니다')
        
        if set_keywords(keywords):
            return success_response(
                data={'keywords': keywords},
                message=f'{len(keywords)}개의 키워드가 저장되었습니다',
                count=len(keywords)
            )
        else:
            return error_response('키워드 저장 실패', 500)
    except Exception as e:
        return error_response(str(e), 500)


