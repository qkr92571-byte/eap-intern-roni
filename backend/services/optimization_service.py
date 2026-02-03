"""
최적화 서비스
- AI를 통한 최적화 제안 생성
- 자동 수정 가능한 항목 식별
- 수정 전/후 코드 비교
"""

import json
import os
from typing import List, Dict, Optional
from pathlib import Path
from dotenv import load_dotenv

from utils.openai_client import get_openai_client
from utils.constants import OPENAI_MODEL_REVIEW
from services.linter_service import lint_file
from services.code_analysis_service import analyze_file

load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent
PROMPTS_DIR = PROJECT_ROOT / 'prompts'
OPTIMIZATION_PROMPT_PATH = PROMPTS_DIR / 'code_optimization_prompt.txt'


def load_optimization_prompt() -> str:
    """최적화 프롬프트 로드"""
    if OPTIMIZATION_PROMPT_PATH.exists():
        with open(OPTIMIZATION_PROMPT_PATH, 'r', encoding='utf-8') as f:
            return f.read()
    return "코드를 분석하고 최적화 제안을 해주세요."


def analyze_code_for_optimization(
    file_path: str,
    code_content: Optional[str] = None
) -> Dict:
    """
    코드 최적화 분석
    
    Args:
        file_path: 파일 경로
        code_content: 코드 내용 (None이면 파일에서 로드)
    
    Returns:
        최적화 분석 결과
    """
    project_root = PROJECT_ROOT.parent
    full_path = project_root / file_path
    
    if code_content is None:
        if not full_path.exists():
            return {
                'success': False,
                'error': f'파일을 찾을 수 없습니다: {file_path}'
            }
        code_content = full_path.read_text(encoding='utf-8')
    
    try:
        # Linter 결과 수집
        linter_results = lint_file(file_path)
        linter_summary = _format_linter_results(linter_results)
        
        # 코드 메트릭 수집
        code_analysis = analyze_file(file_path)
        code_metrics = code_analysis.get('metrics', {})
        metrics_summary = _format_code_metrics(code_metrics)
        
        # 프로젝트 타입 결정
        project_type = 'backend' if file_path.startswith('backend/') else 'frontend'
        
        # AI 최적화 분석 요청
        optimization_result = _request_ai_optimization(
            file_path=file_path,
            code_content=code_content,
            project_type=project_type,
            linter_results=linter_summary,
            code_metrics=metrics_summary
        )
        
        return {
            'success': True,
            'file': file_path,
            'linter_results': linter_results,
            'code_metrics': code_metrics,
            'optimization': optimization_result
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': f'최적화 분석 실패: {str(e)}'
        }


def _format_linter_results(linter_results: List[Dict]) -> str:
    """Linter 결과 포맷팅"""
    if not linter_results:
        return "Linter 이슈 없음"
    
    summary = []
    severity_counts = {'error': 0, 'warning': 0, 'info': 0}
    
    for result in linter_results[:10]:  # 최대 10개만
        severity = result.get('severity', 'info')
        if severity in severity_counts:
            severity_counts[severity] += 1
        summary.append(
            f"Line {result.get('line', 0)}: [{result.get('code', '')}] {result.get('message', '')}"
        )
    
    summary_text = '\n'.join(summary)
    counts_text = f"Errors: {severity_counts['error']}, Warnings: {severity_counts['warning']}, Info: {severity_counts['info']}"
    
    return f"{counts_text}\n{summary_text}"


def _format_code_metrics(metrics: Dict) -> str:
    """코드 메트릭 포맷팅"""
    if not metrics:
        return "메트릭 정보 없음"
    
    lines = metrics.get('total_lines', 0)
    functions = metrics.get('function_count', 0)
    classes = metrics.get('class_count', 0)
    complexity = metrics.get('max_function_complexity', 0)
    
    return f"Lines: {lines}, Functions: {functions}, Classes: {classes}, Max Complexity: {complexity}"


def _request_ai_optimization(
    file_path: str,
    code_content: str,
    project_type: str,
    linter_results: str,
    code_metrics: str
) -> Dict:
    """
    AI를 통한 최적화 분석 요청
    
    Args:
        file_path: 파일 경로
        code_content: 코드 내용
        project_type: 프로젝트 타입 (backend/frontend)
        linter_results: Linter 결과 요약
        code_metrics: 코드 메트릭 요약
    
    Returns:
        AI 최적화 분석 결과
    """
    try:
        client = get_openai_client()
        prompt_template = load_optimization_prompt()
        
        # 프롬프트에 정보 삽입
        prompt = prompt_template.format(
            code_content=code_content[:8000],  # 토큰 제한 고려
            file_path=file_path,
            project_type=project_type,
            linter_results=linter_results[:1000],
            code_metrics=code_metrics
        )
        
        # AI 모델 선택 (환경 변수 또는 기본값)
        model = os.getenv('OPTIMIZATION_MODEL', 'gpt-4o-mini')
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "당신은 코드 품질과 성능을 최적화하는 전문가입니다. 주어진 코드를 분석하고 개선점을 JSON 형식으로 제안해주세요."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=2000,
            temperature=0.3
        )
        
        result_text = response.choices[0].message.content
        
        # JSON 파싱 시도
        try:
            # JSON 코드 블록 추출
            json_match = None
            if '```json' in result_text:
                json_start = result_text.find('```json') + 7
                json_end = result_text.find('```', json_start)
                if json_end > json_start:
                    json_match = result_text[json_start:json_end].strip()
            elif '```' in result_text:
                json_start = result_text.find('```') + 3
                json_end = result_text.find('```', json_start)
                if json_end > json_start:
                    json_match = result_text[json_start:json_end].strip()
            
            if json_match:
                parsed_result = json.loads(json_match)
            else:
                # JSON이 없으면 전체 텍스트를 파싱 시도
                parsed_result = json.loads(result_text)
            
            return {
                'success': True,
                'issues': parsed_result.get('issues', []),
                'metrics': parsed_result.get('metrics', {}),
                'summary': parsed_result.get('summary', ''),
                'raw_response': result_text
            }
        
        except json.JSONDecodeError:
            # JSON 파싱 실패 시 텍스트로 반환
            return {
                'success': True,
                'issues': [],
                'metrics': {},
                'summary': result_text,
                'raw_response': result_text,
                'parse_error': 'JSON 파싱 실패, 텍스트로 반환'
            }
    
    except Exception as e:
        return {
            'success': False,
            'error': f'AI 최적화 분석 실패: {str(e)}'
        }


def identify_auto_fixable_issues(optimization_result: Dict) -> List[Dict]:
    """
    자동 수정 가능한 이슈 식별
    
    Args:
        optimization_result: 최적화 분석 결과
    
    Returns:
        자동 수정 가능한 이슈 리스트
    """
    auto_fixable = []
    
    issues = optimization_result.get('issues', [])
    for issue in issues:
        if issue.get('auto_fixable', False) and issue.get('code_after'):
            auto_fixable.append(issue)
    
    return auto_fixable


def apply_optimization(
    file_path: str,
    issue: Dict,
    backup: bool = True
) -> Dict:
    """
    최적화 적용
    
    Args:
        file_path: 파일 경로
        issue: 최적화 이슈
        backup: 백업 생성 여부
    
    Returns:
        적용 결과
    """
    project_root = PROJECT_ROOT.parent
    full_path = project_root / file_path
    
    if not full_path.exists():
        return {
            'success': False,
            'error': f'파일을 찾을 수 없습니다: {file_path}'
        }
    
    try:
        # 백업 생성
        if backup:
            backup_path = full_path.with_suffix(full_path.suffix + '.backup')
            backup_path.write_text(full_path.read_text(encoding='utf-8'), encoding='utf-8')
        
        # 코드 수정
        current_code = full_path.read_text(encoding='utf-8')
        code_before = issue.get('code_before', '')
        code_after = issue.get('code_after', '')
        
        if code_before and code_after:
            if code_before in current_code:
                new_code = current_code.replace(code_before, code_after, 1)
                full_path.write_text(new_code, encoding='utf-8')
                
                return {
                    'success': True,
                    'file': file_path,
                    'backup': str(backup_path) if backup else None,
                    'changes_applied': True
                }
            else:
                return {
                    'success': False,
                    'error': '코드가 일치하지 않습니다. 파일이 변경되었을 수 있습니다.'
                }
        else:
            return {
                'success': False,
                'error': '수정할 코드가 제공되지 않았습니다.'
            }
    
    except Exception as e:
        return {
            'success': False,
            'error': f'최적화 적용 실패: {str(e)}'
        }

