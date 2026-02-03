"""
OpenAI 클라이언트 공통 유틸리티
- OpenAI 클라이언트 초기화 및 재사용
- 에러 처리 표준화
"""

import os
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv
import openai
import httpx


def _load_env_for_backend():
    """
    backend/.env 또는 프로젝트 루트 .env를 우선적으로 로드
    
    - daily_report 엔트리포인트는 보통 프로젝트 루트에서 실행되므로
      현재 작업 디렉토리 기준 .env만 읽으면 backend/.env를 놓칠 수 있음
    - 이 헬퍼는 다음 우선순위로 .env를 로드한다.
      1) backend/.env
      2) 프로젝트 루트(.env)
      3) 기본 load_dotenv() (마지막 안전장치)
    """
    # 현재 파일 기준으로 backend 디렉토리 위치 계산
    backend_dir = Path(__file__).resolve().parent.parent  # .../backend
    project_root = backend_dir.parent                     # .../ (프로젝트 루트)
    
    backend_env = backend_dir / ".env"
    root_env = project_root / ".env"
    
    if backend_env.exists():
        load_dotenv(backend_env)
    elif root_env.exists():
        load_dotenv(root_env)
    else:
        # 그래도 없으면 기본 동작에 맡김
        load_dotenv()


_load_env_for_backend()

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

