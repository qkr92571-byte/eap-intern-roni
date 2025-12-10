"""
OpenAI 클라이언트 공통 유틸리티
- OpenAI 클라이언트 초기화 및 재사용
- 에러 처리 표준화
"""

import os
from typing import Optional
from dotenv import load_dotenv
import openai
import httpx

load_dotenv()

# OpenAI API 키
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# 전역 클라이언트 인스턴스 (재사용)
_client: Optional[openai.OpenAI] = None


def get_openai_client() -> openai.OpenAI:
    """
    OpenAI 클라이언트 인스턴스 반환 (싱글톤 패턴)
    
    Returns:
        OpenAI 클라이언트 인스턴스
        
    Raises:
        ValueError: OPENAI_API_KEY가 설정되지 않은 경우
    """
    global _client
    
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다. .env 파일에 OPENAI_API_KEY를 추가해주세요.")
    
    if _client is None:
        # httpx 클라이언트를 명시적으로 생성하여 proxies 문제 해결
        http_client = httpx.Client(timeout=60.0)
        _client = openai.OpenAI(
            api_key=OPENAI_API_KEY,
            http_client=http_client
        )
    
    return _client


def reset_client():
    """클라이언트 인스턴스 리셋 (테스트용)"""
    global _client
    _client = None

