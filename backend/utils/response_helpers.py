"""
API 응답 헬퍼 함수
"""

from flask import jsonify
from typing import Any, Optional

def success_response(data: Any = None, message: Optional[str] = None, count: Optional[int] = None):
    """
    성공 응답 생성
    
    Args:
        data: 응답 데이터
        message: 성공 메시지
        count: 데이터 개수
        
    Returns:
        JSON 응답
    """
    response = {'success': True}
    
    if data is not None:
        response['data'] = data
    
    if message:
        response['message'] = message
    
    if count is not None:
        response['count'] = count
    
    return jsonify(response)

def error_response(error: str, status_code: int = 500):
    """
    에러 응답 생성
    
    Args:
        error: 에러 메시지
        status_code: HTTP 상태 코드
        
    Returns:
        JSON 응답
    """
    return jsonify({
        'success': False,
        'error': error
    }), status_code

def not_found_response(message: str = '리소스를 찾을 수 없습니다'):
    """
    404 응답 생성
    
    Args:
        message: 에러 메시지
        
    Returns:
        JSON 응답
    """
    return error_response(message, 404)

def bad_request_response(message: str = '잘못된 요청입니다'):
    """
    400 응답 생성
    
    Args:
        message: 에러 메시지
        
    Returns:
        JSON 응답
    """
    return error_response(message, 400)


