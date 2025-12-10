"""
로깅 유틸리티
- 일관된 로깅 포맷 제공
- 단계별 진행 상황 표시
"""

from typing import Optional
from datetime import datetime


class StepLogger:
    """단계별 로깅을 위한 헬퍼 클래스"""
    
    def __init__(self, step_name: str, total_steps: Optional[int] = None):
        self.step_name = step_name
        self.total_steps = total_steps
        self.current_step = 0
    
    def start(self):
        """단계 시작"""
        print("=" * 60)
        print(self.step_name)
        print("=" * 60)
    
    def info(self, message: str):
        """정보 메시지"""
        print(f"   {message}")
    
    def success(self, message: str):
        """성공 메시지"""
        print(f"   ✅ {message}")
    
    def warning(self, message: str):
        """경고 메시지"""
        print(f"   ⚠️  {message}")
    
    def error(self, message: str):
        """에러 메시지"""
        print(f"   ❌ {message}")
    
    def progress(self, current: int, message: str = ""):
        """진행 상황 표시"""
        if self.total_steps:
            print(f"   [{current}/{self.total_steps}] {message}")
        else:
            print(f"   [{current}] {message}")
    
    def section(self, title: str):
        """섹션 구분"""
        print(f"\n{'-' * 60}")
        print(title)
        print("-" * 60)


def log_step(step_num: int, total_steps: int, message: str, icon: str = ""):
    """단계 로깅 헬퍼"""
    prefix = f"[{step_num}/{total_steps}]"
    if icon:
        print(f"   {prefix} {icon} {message}")
    else:
        print(f"   {prefix} {message}")


def log_success(message: str):
    """성공 로깅"""
    print(f"✅ {message}")


def log_error(message: str):
    """에러 로깅"""
    print(f"❌ {message}")


def log_warning(message: str):
    """경고 로깅"""
    print(f"⚠️  {message}")


def log_info(message: str):
    """정보 로깅"""
    print(f"ℹ️  {message}")


def log_section(title: str):
    """섹션 구분"""
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)

