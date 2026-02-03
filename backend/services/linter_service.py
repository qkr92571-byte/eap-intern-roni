"""
Linter 통합 서비스
- Python linter 통합 (pylint, flake8)
- TypeScript/JavaScript linter 통합 (eslint)
- linter 결과 파싱 및 정규화
"""

import subprocess
import json
import os
from typing import List, Dict, Optional
from pathlib import Path
from enum import Enum


class LinterType(Enum):
    """Linter 타입"""
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    JAVASCRIPT = "javascript"


class LinterSeverity(Enum):
    """Linter 심각도"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    HINT = "hint"


def get_project_root() -> Path:
    """프로젝트 루트 디렉토리 반환"""
    current = Path(__file__).parent.parent.parent
    while current != current.parent:
        if (current / '.git').exists() or (current / 'backend').exists():
            return current
        current = current.parent
    return Path(__file__).parent.parent.parent


def check_linter_installed(linter_name: str) -> bool:
    """Linter가 설치되어 있는지 확인"""
    try:
        result = subprocess.run(
            [linter_name, '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def run_pylint(file_path: str) -> List[Dict]:
    """
    pylint 실행
    
    Args:
        file_path: Python 파일 경로
    
    Returns:
        linter 결과 리스트
    """
    if not check_linter_installed('pylint'):
        return []
    
    project_root = get_project_root()
    full_path = project_root / file_path
    
    if not full_path.exists() or not file_path.endswith('.py'):
        return []
    
    results = []
    
    try:
        # pylint를 JSON 형식으로 실행
        result = subprocess.run(
            ['pylint', '--output-format=json', str(full_path)],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode in [0, 1]:  # 0: 성공, 1: 이슈 발견
            try:
                pylint_output = json.loads(result.stdout)
                for issue in pylint_output:
                    severity_map = {
                        'error': LinterSeverity.ERROR,
                        'warning': LinterSeverity.WARNING,
                        'info': LinterSeverity.INFO,
                        'convention': LinterSeverity.HINT
                    }
                    
                    results.append({
                        'file': file_path,
                        'line': issue.get('line', 0),
                        'column': issue.get('column', 0),
                        'message': issue.get('message', ''),
                        'code': issue.get('message-id', ''),
                        'severity': severity_map.get(
                            issue.get('type', 'info').lower(),
                            LinterSeverity.INFO
                        ).value,
                        'linter': 'pylint'
                    })
            except json.JSONDecodeError:
                # JSON 파싱 실패 시 텍스트 파싱 시도
                pass
    
    except subprocess.TimeoutExpired:
        print(f"⚠️  pylint 실행 시간 초과: {file_path}")
    except Exception as e:
        print(f"⚠️  pylint 실행 실패 ({file_path}): {str(e)}")
    
    return results


def run_flake8(file_path: str) -> List[Dict]:
    """
    flake8 실행
    
    Args:
        file_path: Python 파일 경로
    
    Returns:
        linter 결과 리스트
    """
    if not check_linter_installed('flake8'):
        return []
    
    project_root = get_project_root()
    full_path = project_root / file_path
    
    if not full_path.exists() or not file_path.endswith('.py'):
        return []
    
    results = []
    
    try:
        result = subprocess.run(
            ['flake8', '--format=default', str(full_path)],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # flake8는 이슈가 있으면 1을 반환
        if result.returncode == 1:
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                
                # flake8 출력 형식: file:line:column: code message
                parts = line.split(':', 3)
                if len(parts) >= 4:
                    rel_path = Path(parts[0]).relative_to(project_root)
                    line_num = int(parts[1]) if parts[1].isdigit() else 0
                    col_num = int(parts[2]) if parts[2].isdigit() else 0
                    code_and_message = parts[3].strip().split(' ', 1)
                    code = code_and_message[0] if code_and_message else ''
                    message = code_and_message[1] if len(code_and_message) > 1 else ''
                    
                    # 코드로 심각도 판단
                    severity = LinterSeverity.WARNING.value
                    if code.startswith('E9') or code.startswith('F'):
                        severity = LinterSeverity.ERROR.value
                    elif code.startswith('E'):
                        severity = LinterSeverity.ERROR.value
                    elif code.startswith('W'):
                        severity = LinterSeverity.WARNING.value
                    
                    results.append({
                        'file': str(rel_path),
                        'line': line_num,
                        'column': col_num,
                        'message': message,
                        'code': code,
                        'severity': severity,
                        'linter': 'flake8'
                    })
    
    except subprocess.TimeoutExpired:
        print(f"⚠️  flake8 실행 시간 초과: {file_path}")
    except Exception as e:
        print(f"⚠️  flake8 실행 실패 ({file_path}): {str(e)}")
    
    return results


def run_eslint(file_path: str) -> List[Dict]:
    """
    eslint 실행
    
    Args:
        file_path: TypeScript/JavaScript 파일 경로
    
    Returns:
        linter 결과 리스트
    """
    project_root = get_project_root()
    frontend_dir = project_root / 'frontend'
    
    if not frontend_dir.exists():
        return []
    
    # eslint는 frontend 디렉토리에서 실행
    if not (file_path.startswith('frontend/') and 
            (file_path.endswith('.ts') or file_path.endswith('.tsx') or 
             file_path.endswith('.js') or file_path.endswith('.jsx'))):
        return []
    
    full_path = project_root / file_path
    
    if not full_path.exists():
        return []
    
    results = []
    
    try:
        # eslint를 JSON 형식으로 실행
        result = subprocess.run(
            ['npx', 'eslint', '--format=json', str(full_path)],
            cwd=frontend_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # eslint는 이슈가 있으면 1을 반환
        if result.returncode == 1:
            try:
                eslint_output = json.loads(result.stdout)
                for file_result in eslint_output:
                    rel_path = Path(file_result.get('filePath', '')).relative_to(project_root)
                    for message in file_result.get('messages', []):
                        severity_map = {
                            2: LinterSeverity.ERROR,
                            1: LinterSeverity.WARNING,
                            0: LinterSeverity.INFO
                        }
                        
                        results.append({
                            'file': str(rel_path),
                            'line': message.get('line', 0),
                            'column': message.get('column', 0),
                            'message': message.get('message', ''),
                            'code': message.get('ruleId', ''),
                            'severity': severity_map.get(
                                message.get('severity', 0),
                                LinterSeverity.INFO
                            ).value,
                            'linter': 'eslint'
                        })
            except json.JSONDecodeError:
                pass
    
    except subprocess.TimeoutExpired:
        print(f"⚠️  eslint 실행 시간 초과: {file_path}")
    except FileNotFoundError:
        # npx가 없거나 eslint가 설치되지 않음
        pass
    except Exception as e:
        print(f"⚠️  eslint 실행 실패 ({file_path}): {str(e)}")
    
    return results


def lint_file(file_path: str, linters: Optional[List[str]] = None) -> List[Dict]:
    """
    파일에 대해 적절한 linter 실행
    
    Args:
        file_path: 파일 경로
        linters: 실행할 linter 목록 (None이면 자동 감지)
    
    Returns:
        모든 linter 결과 통합 리스트
    """
    all_results = []
    
    # 파일 타입에 따라 자동 감지
    if file_path.endswith('.py'):
        if linters is None or 'pylint' in linters:
            all_results.extend(run_pylint(file_path))
        if linters is None or 'flake8' in linters:
            all_results.extend(run_flake8(file_path))
    elif file_path.endswith(('.ts', '.tsx', '.js', '.jsx')):
        if linters is None or 'eslint' in linters:
            all_results.extend(run_eslint(file_path))
    
    return all_results


def lint_directory(directory: str, recursive: bool = True) -> Dict[str, List[Dict]]:
    """
    디렉토리 내 모든 파일에 대해 linter 실행
    
    Args:
        directory: 디렉토리 경로
        recursive: 재귀적으로 검사할지 여부
    
    Returns:
        파일별 linter 결과 딕셔너리
    """
    project_root = get_project_root()
    target_dir = project_root / directory
    
    if not target_dir.exists() or not target_dir.is_dir():
        return {}
    
    results = {}
    
    # Python 파일
    pattern = '**/*.py' if recursive else '*.py'
    for py_file in target_dir.glob(pattern):
        rel_path = str(py_file.relative_to(project_root))
        file_results = lint_file(rel_path)
        if file_results:
            results[rel_path] = file_results
    
    # TypeScript/JavaScript 파일
    for ext in ['*.ts', '*.tsx', '*.js', '*.jsx']:
        pattern = f'**/{ext}' if recursive else ext
        for js_file in target_dir.glob(pattern):
            rel_path = str(js_file.relative_to(project_root))
            file_results = lint_file(rel_path)
            if file_results:
                results[rel_path] = file_results
    
    return results


def aggregate_linter_results(results: Dict[str, List[Dict]]) -> Dict:
    """
    Linter 결과 집계
    
    Args:
        results: 파일별 linter 결과
    
    Returns:
        집계된 통계 정보
    """
    total_files = len(results)
    total_issues = sum(len(issues) for issues in results.values())
    
    severity_counts = {
        'error': 0,
        'warning': 0,
        'info': 0,
        'hint': 0
    }
    
    linter_counts = {}
    
    for file_results in results.values():
        for issue in file_results:
            severity = issue.get('severity', 'info')
            if severity in severity_counts:
                severity_counts[severity] += 1
            
            linter_name = issue.get('linter', 'unknown')
            linter_counts[linter_name] = linter_counts.get(linter_name, 0) + 1
    
    return {
        'total_files': total_files,
        'total_issues': total_issues,
        'severity_counts': severity_counts,
        'linter_counts': linter_counts,
        'files_with_issues': len([f for f, issues in results.items() if issues])
    }

