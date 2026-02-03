"""
Orchestration 모듈
- 사용자 의도를 해석하여 에이전트/스킬 실행 순서 결정
- 컨펌 정책 관리
"""

# 순환 import 방지를 위해 policies만 import
from .policies import ConfirmPolicy, should_confirm, request_confirmation

__all__ = [
    'ConfirmPolicy',
    'should_confirm',
    'request_confirmation',
    'Orchestrator',
]

# Orchestrator는 lazy import로 처리 (순환 참조 방지)
def __getattr__(name):
    if name == 'Orchestrator':
        from .orchestrator import Orchestrator
        return Orchestrator
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
