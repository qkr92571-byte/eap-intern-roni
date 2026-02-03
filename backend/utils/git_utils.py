"""
Git 유틸리티
- Git diff 분석
- 변경된 파일 목록 추출
- 커밋 히스토리 분석
"""

import subprocess
import os
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime


def get_project_root() -> Path:
    """프로젝트 루트 디렉토리 반환"""
    current = Path(__file__).parent.parent.parent
    # .git 디렉토리를 찾을 때까지 상위로 이동
    while current != current.parent:
        if (current / '.git').exists():
            return current
        current = current.parent
    # .git이 없으면 현재 디렉토리 반환
    return Path(__file__).parent.parent.parent


def is_git_repository() -> bool:
    """현재 디렉토리가 Git 저장소인지 확인"""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--git-dir'],
            cwd=get_project_root(),
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def get_changed_files(commit: Optional[str] = None, staged: bool = False) -> List[str]:
    """
    변경된 파일 목록 추출
    
    Args:
        commit: 커밋 해시 (None이면 현재 변경사항)
        staged: staged 파일만 가져올지 여부
    
    Returns:
        변경된 파일 경로 리스트
    """
    if not is_git_repository():
        return []
    
    project_root = get_project_root()
    changed_files = []
    
    try:
        if commit:
            # 특정 커밋과 그 이전 커밋 간의 차이
            result = subprocess.run(
                ['git', 'diff', '--name-only', f'{commit}^..{commit}'],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=10
            )
        elif staged:
            # staged 파일만
            result = subprocess.run(
                ['git', 'diff', '--cached', '--name-only'],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=10
            )
        else:
            # 현재 변경사항 (unstaged)
            result = subprocess.run(
                ['git', 'diff', '--name-only'],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=10
            )
        
        if result.returncode == 0:
            changed_files = [
                line.strip() 
                for line in result.stdout.strip().split('\n') 
                if line.strip()
            ]
    
    except subprocess.TimeoutExpired:
        print("⚠️  Git 명령 실행 시간 초과")
    except Exception as e:
        print(f"⚠️  Git 파일 목록 조회 실패: {str(e)}")
    
    return changed_files


def get_file_diff(file_path: str, commit: Optional[str] = None) -> str:
    """
    파일의 diff 내용 가져오기
    
    Args:
        file_path: 파일 경로 (프로젝트 루트 기준)
        commit: 커밋 해시 (None이면 현재 변경사항)
    
    Returns:
        diff 내용 문자열
    """
    if not is_git_repository():
        return ""
    
    project_root = get_project_root()
    full_path = project_root / file_path
    
    if not full_path.exists():
        return ""
    
    try:
        if commit:
            # 특정 커밋의 파일 내용
            result = subprocess.run(
                ['git', 'show', f'{commit}:{file_path}'],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                old_content = result.stdout
                # 현재 파일 내용과 비교
                current_content = full_path.read_text(encoding='utf-8')
                # 간단한 diff 생성 (실제로는 git diff 사용 권장)
                return f"--- {file_path} (커밋 {commit[:8]})\n+++ {file_path} (현재)\n{_simple_diff(old_content, current_content)}"
        else:
            # 현재 변경사항
            result = subprocess.run(
                ['git', 'diff', file_path],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return result.stdout
    
    except subprocess.TimeoutExpired:
        print(f"⚠️  Git diff 실행 시간 초과: {file_path}")
    except Exception as e:
        print(f"⚠️  Git diff 조회 실패 ({file_path}): {str(e)}")
    
    return ""


def _simple_diff(old_content: str, new_content: str) -> str:
    """간단한 diff 생성 (실제로는 git diff 사용 권장)"""
    old_lines = old_content.splitlines()
    new_lines = new_content.splitlines()
    
    diff_lines = []
    max_len = max(len(old_lines), len(new_lines))
    
    for i in range(max_len):
        old_line = old_lines[i] if i < len(old_lines) else None
        new_line = new_lines[i] if i < len(new_lines) else None
        
        if old_line != new_line:
            if old_line is not None:
                diff_lines.append(f"-{old_line}")
            if new_line is not None:
                diff_lines.append(f"+{new_line}")
    
    return '\n'.join(diff_lines)


def get_commit_info(commit: str) -> Dict:
    """
    커밋 정보 가져오기
    
    Args:
        commit: 커밋 해시
    
    Returns:
        커밋 정보 딕셔너리
    """
    if not is_git_repository():
        return {}
    
    project_root = get_project_root()
    info = {
        'hash': commit,
        'message': '',
        'author': '',
        'date': '',
        'files': []
    }
    
    try:
        # 커밋 메시지
        result = subprocess.run(
            ['git', 'log', '-1', '--pretty=format:%s', commit],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            info['message'] = result.stdout.strip()
        
        # 커밋 작성자
        result = subprocess.run(
            ['git', 'log', '-1', '--pretty=format:%an', commit],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            info['author'] = result.stdout.strip()
        
        # 커밋 날짜
        result = subprocess.run(
            ['git', 'log', '-1', '--pretty=format:%ai', commit],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            info['date'] = result.stdout.strip()
        
        # 변경된 파일 목록
        info['files'] = get_changed_files(commit=commit)
    
    except subprocess.TimeoutExpired:
        print(f"⚠️  Git 커밋 정보 조회 시간 초과: {commit}")
    except Exception as e:
        print(f"⚠️  Git 커밋 정보 조회 실패 ({commit}): {str(e)}")
    
    return info


def filter_code_files(file_paths: List[str]) -> List[str]:
    """
    코드 파일만 필터링
    
    Args:
        file_paths: 파일 경로 리스트
    
    Returns:
        코드 파일 경로 리스트
    """
    code_extensions = {
        '.py', '.ts', '.tsx', '.js', '.jsx',
        '.json', '.yaml', '.yml', '.md'
    }
    
    code_files = []
    for file_path in file_paths:
        # 확장자 확인
        if any(file_path.endswith(ext) for ext in code_extensions):
            # 제외할 디렉토리/파일
            excluded_patterns = [
                'node_modules', '__pycache__', '.git',
                'build', 'dist', '.venv', 'venv',
                'downloads', 'history', 'report'
            ]
            if not any(pattern in file_path for pattern in excluded_patterns):
                code_files.append(file_path)
    
    return code_files


def get_recent_commits(limit: int = 10) -> List[Dict]:
    """
    최근 커밋 목록 가져오기
    
    Args:
        limit: 가져올 커밋 수
    
    Returns:
        커밋 정보 리스트
    """
    if not is_git_repository():
        return []
    
    project_root = get_project_root()
    commits = []
    
    try:
        result = subprocess.run(
            ['git', 'log', f'-{limit}', '--pretty=format:%H|%s|%an|%ai'],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                parts = line.split('|', 3)
                if len(parts) == 4:
                    commits.append({
                        'hash': parts[0],
                        'message': parts[1],
                        'author': parts[2],
                        'date': parts[3]
                    })
    
    except subprocess.TimeoutExpired:
        print("⚠️  Git 커밋 목록 조회 시간 초과")
    except Exception as e:
        print(f"⚠️  Git 커밋 목록 조회 실패: {str(e)}")
    
    return commits

