"""
코드 변경 안전성 검사기
- 변경사항 위험도 평가
- 테스트 파일 영향도 확인
- 핵심 비즈니스 로직 보호
- 자동 수정 가능 여부 판단
"""

from typing import Dict, List, Optional, Tuple
from pathlib import Path
from enum import Enum


class RiskLevel(Enum):
    """위험도 레벨"""
    SAFE = "safe"  # 안전 - 자동 수정 가능
    CAUTION = "caution"  # 주의 - 사용자 확인 필요
    DANGEROUS = "dangerous"  # 위험 - 수정 금지


class ChangeType(Enum):
    """변경 타입"""
    FORMATTING = "formatting"  # 포맷팅만 변경
    REFACTORING = "refactoring"  # 리팩토링
    LOGIC_CHANGE = "logic_change"  # 로직 변경
    API_CHANGE = "api_change"  # API 변경
    CONFIG_CHANGE = "config_change"  # 설정 변경


def get_project_root() -> Path:
    """프로젝트 루트 디렉토리 반환"""
    current = Path(__file__).parent.parent.parent
    while current != current.parent:
        if (current / '.git').exists() or (current / 'backend').exists():
            return current
        current = current.parent
    return Path(__file__).parent.parent.parent


# 보호해야 할 핵심 파일/디렉토리 패턴
PROTECTED_PATTERNS = [
    'config/',  # 설정 파일
    '.env',  # 환경 변수
    'firebase',  # Firebase 키 파일
    'test_',  # 테스트 파일
    '_test.py',  # 테스트 파일
    'tests/',  # 테스트 디렉토리
    '__pycache__/',  # 캐시 디렉토리
    'node_modules/',  # Node 모듈
    'venv/',  # 가상 환경
    '.venv/',
    'downloads/',  # 다운로드 파일
    'history/',  # 히스토리 파일
    'report/',  # 리포트 파일
]

# 핵심 비즈니스 로직 파일
CRITICAL_FILES = [
    'firebase_service.py',  # Firebase 연동
    'scraper_service.py',  # 스크래핑 로직
    'review_service.py',  # 검수 로직
    'workflow_service.py',  # 워크플로우
    'app.py',  # Flask 앱
]

# 자동 수정 가능한 변경 타입
AUTO_FIXABLE_CHANGES = [
    'whitespace',  # 공백 정리
    'import_order',  # 임포트 순서
    'unused_import',  # 사용하지 않는 임포트 제거
    'variable_naming',  # 변수명 스타일 (안전한 경우만)
    'type_hint',  # 타입 힌트 추가
    'docstring_format',  # 독스트링 포맷
]


def is_protected_file(file_path: str) -> bool:
    """
    보호된 파일인지 확인
    
    Args:
        file_path: 파일 경로
    
    Returns:
        보호 여부
    """
    file_path_lower = file_path.lower()
    
    for pattern in PROTECTED_PATTERNS:
        if pattern in file_path_lower:
            return True
    
    return False


def is_critical_file(file_path: str) -> bool:
    """
    핵심 비즈니스 로직 파일인지 확인
    
    Args:
        file_path: 파일 경로
    
    Returns:
        핵심 파일 여부
    """
    file_name = Path(file_path).name
    
    return file_name in CRITICAL_FILES


def is_test_file(file_path: str) -> bool:
    """
    테스트 파일인지 확인
    
    Args:
        file_path: 파일 경로
    
    Returns:
        테스트 파일 여부
    """
    file_path_lower = file_path.lower()
    file_name = Path(file_path).name.lower()
    
    test_patterns = ['test_', '_test', 'tests/', '__test__']
    
    for pattern in test_patterns:
        if pattern in file_path_lower or pattern in file_name:
            return True
    
    return False


def assess_change_risk(
    file_path: str,
    change_type: str,
    old_code: Optional[str] = None,
    new_code: Optional[str] = None
) -> Tuple[RiskLevel, str]:
    """
    변경사항 위험도 평가
    
    Args:
        file_path: 파일 경로
        change_type: 변경 타입
        old_code: 변경 전 코드
        new_code: 변경 후 코드
    
    Returns:
        (위험도, 사유) 튜플
    """
    # 보호된 파일은 수정 금지
    if is_protected_file(file_path):
        return RiskLevel.DANGEROUS, "보호된 파일/디렉토리입니다"
    
    # 테스트 파일은 수정하지 않음
    if is_test_file(file_path):
        return RiskLevel.DANGEROUS, "테스트 파일은 수정하지 않습니다"
    
    # 자동 수정 가능한 변경은 안전
    if change_type in AUTO_FIXABLE_CHANGES:
        return RiskLevel.SAFE, "자동 수정 가능한 변경입니다"
    
    # 핵심 파일의 로직 변경은 위험
    if is_critical_file(file_path):
        if change_type in ['logic_change', 'api_change']:
            return RiskLevel.DANGEROUS, "핵심 비즈니스 로직 파일의 로직 변경은 위험합니다"
        elif change_type == 'refactoring':
            return RiskLevel.CAUTION, "핵심 파일의 리팩토링은 주의가 필요합니다"
    
    # 코드 비교를 통한 위험도 평가
    if old_code and new_code:
        risk, reason = _compare_code_changes(old_code, new_code)
        if risk:
            return risk, reason
    
    # 기본값: 주의
    return RiskLevel.CAUTION, "변경사항을 검토해야 합니다"


def _compare_code_changes(old_code: str, new_code: str) -> Tuple[Optional[RiskLevel], str]:
    """
    코드 변경 비교
    
    Args:
        old_code: 변경 전 코드
        new_code: 변경 후 코드
    
    Returns:
        (위험도, 사유) 튜플 (위험도가 None이면 기본 평가 사용)
    """
    old_lines = old_code.splitlines()
    new_lines = new_code.splitlines()
    
    # 라인 수가 크게 변경되면 주의
    line_diff = abs(len(new_lines) - len(old_lines))
    if line_diff > len(old_lines) * 0.3:  # 30% 이상 변경
        return RiskLevel.CAUTION, "코드 변경량이 큽니다"
    
    # 함수/클래스 정의 변경 확인 (간단한 버전)
    old_defs = [line for line in old_lines if line.strip().startswith(('def ', 'class '))]
    new_defs = [line for line in new_lines if line.strip().startswith(('def ', 'class '))]
    
    if len(old_defs) != len(new_defs):
        return RiskLevel.CAUTION, "함수/클래스 정의가 변경되었습니다"
    
    # 기본값: None (기본 평가 사용)
    return None, ""


def can_auto_fix(file_path: str, change_type: str, change_description: str) -> bool:
    """
    자동 수정 가능 여부 판단
    
    Args:
        file_path: 파일 경로
        change_type: 변경 타입
        change_description: 변경 설명
    
    Returns:
        자동 수정 가능 여부
    """
    # 보호된 파일은 수정 불가
    if is_protected_file(file_path):
        return False
    
    # 테스트 파일은 수정 불가
    if is_test_file(file_path):
        return False
    
    # 자동 수정 가능한 변경 타입
    if change_type in AUTO_FIXABLE_CHANGES:
        return True
    
    # 핵심 파일은 자동 수정 불가 (안전한 변경만)
    if is_critical_file(file_path):
        return change_type in ['formatting', 'import_order', 'unused_import', 'docstring_format']
    
    # 기본값: 주의가 필요한 변경은 자동 수정 불가
    return False


def check_test_impact(file_path: str) -> Dict:
    """
    테스트 영향도 확인
    
    Args:
        file_path: 파일 경로
    
    Returns:
        테스트 영향도 정보
    """
    project_root = get_project_root()
    file_name = Path(file_path).stem
    
    # 관련 테스트 파일 찾기
    test_files = []
    
    # backend/tests 또는 프로젝트 내 test_*.py 파일 찾기
    for test_dir in [project_root / 'backend' / 'tests', project_root / 'tests']:
        if test_dir.exists():
            for test_file in test_dir.glob('**/*.py'):
                if 'test' in test_file.name.lower():
                    # 파일명 기반 매칭 (간단한 버전)
                    if file_name.replace('_service', '').replace('_routes', '') in test_file.stem:
                        test_files.append(str(test_file.relative_to(project_root)))
    
    return {
        'has_tests': len(test_files) > 0,
        'test_files': test_files,
        'impact_level': 'high' if test_files else 'unknown'
    }


def validate_change(
    file_path: str,
    change_type: str,
    old_code: Optional[str] = None,
    new_code: Optional[str] = None,
    change_description: str = ""
) -> Dict:
    """
    변경사항 검증
    
    Args:
        file_path: 파일 경로
        change_type: 변경 타입
        old_code: 변경 전 코드
        new_code: 변경 후 코드
        change_description: 변경 설명
    
    Returns:
        검증 결과 딕셔너리
    """
    risk_level, risk_reason = assess_change_risk(file_path, change_type, old_code, new_code)
    auto_fixable = can_auto_fix(file_path, change_type, change_description)
    test_impact = check_test_impact(file_path)
    
    return {
        'file': file_path,
        'change_type': change_type,
        'risk_level': risk_level.value,
        'risk_reason': risk_reason,
        'auto_fixable': auto_fixable,
        'test_impact': test_impact,
        'recommendation': _get_recommendation(risk_level, auto_fixable)
    }


def _get_recommendation(risk_level: RiskLevel, auto_fixable: bool) -> str:
    """권장사항 생성"""
    if risk_level == RiskLevel.SAFE and auto_fixable:
        return "자동 수정 가능"
    elif risk_level == RiskLevel.SAFE:
        return "안전하게 수정 가능하지만 수동 확인 권장"
    elif risk_level == RiskLevel.CAUTION:
        return "사용자 확인 후 수정 권장"
    else:
        return "수정하지 않는 것을 권장합니다"

