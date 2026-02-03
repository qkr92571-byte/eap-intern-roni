"""
컨펌 정책 관리

규칙:
- 'interactive': DB 쓰기·슬랙 전송 전에 사용자에게 확인 (기본값)
- 'auto': 명시적 플래그(--auto 또는 AUTO_CONFIRM=1)가 있을 때만 자동 실행
"""

import os
from enum import Enum
from typing import Optional


class ConfirmPolicy(Enum):
    """컨펌 정책"""
    INTERACTIVE = 'interactive'  # 사용자 확인 필요
    AUTO = 'auto'  # 자동 실행 (명시적 플래그 필요)


def should_confirm(policy: str) -> bool:
    """
    컨펌이 필요한지 확인
    
    Args:
        policy: 컨펌 정책 ('interactive' 또는 'auto')
    
    Returns:
        컨펌이 필요하면 True
    """
    if policy == ConfirmPolicy.AUTO.value:
        # AUTO_CONFIRM 환경변수 확인
        auto_confirm = os.getenv('AUTO_CONFIRM', '').strip().lower()
        if auto_confirm in ('1', 'true', 'yes'):
            return False  # 자동 모드
        return True  # 명시적 플래그가 없으면 컨펌 필요
    
    # interactive 모드는 항상 컨펌 필요
    return True


def request_confirmation(prompt: str = "계속하시겠습니까? (yes/no): ") -> bool:
    """
    사용자에게 컨펌 요청
    
    Args:
        prompt: 컨펌 프롬프트 메시지
    
    Returns:
        사용자가 yes/y를 입력하면 True
    """
    user_input = input(f"   {prompt}").strip().lower()
    return user_input in ('yes', 'y')
