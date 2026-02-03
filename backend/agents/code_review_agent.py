"""
코드리뷰 에이전트
- Git diff 또는 지정된 파일 분석
- 변경된 코드 추출
- 코드 메트릭 수집
- AI 전문가 리뷰 요청
- 개선점 및 제안사항 수집
- JSON 리포트 생성
"""

import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from dotenv import load_dotenv

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.git_utils import (
    get_changed_files,
    get_file_diff,
    get_commit_info,
    filter_code_files,
    is_git_repository
)
from services.code_analysis_service import analyze_file
from utils.openai_client import get_openai_client
from utils.logger import StepLogger

load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent.parent
PROMPTS_DIR = PROJECT_ROOT / 'backend' / 'prompts'
REVIEW_PROMPT_PATH = PROMPTS_DIR / 'code_review_prompt.txt'
OUTPUT_DIR = PROJECT_ROOT / 'backend' / 'code_analysis' / 'review_reports'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_review_prompt() -> str:
    """코드리뷰 프롬프트 로드"""
    if REVIEW_PROMPT_PATH.exists():
        with open(REVIEW_PROMPT_PATH, 'r', encoding='utf-8') as f:
            return f.read()
    return "코드를 리뷰하고 개선점을 제안해주세요."


def request_ai_review(
    file_path: str,
    old_code: str,
    new_code: str,
    change_description: str = "",
    code_metrics: Optional[Dict] = None
) -> Dict:
    """
    AI를 통한 코드리뷰 요청
    
    Args:
        file_path: 파일 경로
        old_code: 변경 전 코드
        new_code: 변경 후 코드
        change_description: 변경 설명
        code_metrics: 코드 메트릭
    
    Returns:
        리뷰 결과
    """
    try:
        client = get_openai_client()
        prompt_template = load_review_prompt()
        
        # 코드 메트릭 포맷팅
        metrics_text = ""
        if code_metrics:
            lines = code_metrics.get('total_lines', 0)
            functions = code_metrics.get('function_count', 0)
            classes = code_metrics.get('class_count', 0)
            metrics_text = f"Lines: {lines}, Functions: {functions}, Classes: {classes}"
        
        # 프로젝트 타입 결정
        project_type = 'backend' if file_path.startswith('backend/') else 'frontend'
        
        # 프롬프트에 정보 삽입
        prompt = prompt_template.format(
            old_code=old_code[:4000],  # 토큰 제한 고려
            new_code=new_code[:4000],
            change_description=change_description or "코드 변경",
            file_path=file_path,
            project_type=project_type,
            code_metrics=metrics_text,
            related_files=""
        )
        
        # AI 모델 선택
        model = os.getenv('REVIEW_MODEL', 'gpt-4o-mini')
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "당신은 경험이 풍부한 시니어 개발자이자 코드리뷰 전문가입니다. 주어진 코드 변경사항을 전문가 수준으로 리뷰하고 개선점을 JSON 형식으로 제안해주세요."
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
                parsed_result = json.loads(result_text)
            
            return {
                'success': True,
                'overall_rating': parsed_result.get('overall_rating', 'unknown'),
                'summary': parsed_result.get('summary', ''),
                'strengths': parsed_result.get('strengths', []),
                'issues': parsed_result.get('issues', []),
                'suggestions': parsed_result.get('suggestions', []),
                'questions': parsed_result.get('questions', []),
                'raw_response': result_text
            }
        
        except json.JSONDecodeError:
            # JSON 파싱 실패 시 텍스트로 반환
            return {
                'success': True,
                'overall_rating': 'unknown',
                'summary': result_text,
                'strengths': [],
                'issues': [],
                'suggestions': [],
                'questions': [],
                'raw_response': result_text,
                'parse_error': 'JSON 파싱 실패, 텍스트로 반환'
            }
    
    except Exception as e:
        return {
            'success': False,
            'error': f'AI 리뷰 요청 실패: {str(e)}'
        }


def review_file_changes(
    file_path: str,
    old_code: Optional[str] = None,
    new_code: Optional[str] = None
) -> Dict:
    """
    파일 변경사항 리뷰
    
    Args:
        file_path: 파일 경로
        old_code: 변경 전 코드 (None이면 Git에서 가져옴)
        new_code: 변경 후 코드 (None이면 현재 파일)
    
    Returns:
        리뷰 결과
    """
    project_root = PROJECT_ROOT
    full_path = project_root / file_path
    
    # 현재 코드 로드
    if new_code is None:
        if full_path.exists():
            new_code = full_path.read_text(encoding='utf-8')
        else:
            return {
                'success': False,
                'error': f'파일을 찾을 수 없습니다: {file_path}'
            }
    
    # 변경 전 코드 (Git diff 또는 제공된 코드)
    if old_code is None:
        if is_git_repository():
            diff = get_file_diff(file_path)
            # 간단한 diff 파싱 (실제로는 더 정교한 파싱 필요)
            old_code = new_code  # 기본값: 현재 코드와 동일
        else:
            old_code = new_code
    
    # 코드 분석
    code_analysis = analyze_file(file_path)
    code_metrics = code_analysis.get('metrics', {})
    
    # AI 리뷰 요청
    review_result = request_ai_review(
        file_path=file_path,
        old_code=old_code,
        new_code=new_code,
        change_description="코드 변경",
        code_metrics=code_metrics
    )
    
    return {
        'file': file_path,
        'code_metrics': code_metrics,
        'review': review_result
    }


def run_review_agent(
    commit: Optional[str] = None,
    files: Optional[List[str]] = None,
    output_file: Optional[str] = None
) -> Dict:
    """
    코드리뷰 에이전트 실행
    
    Args:
        commit: 커밋 해시 (None이면 현재 변경사항)
        files: 리뷰할 파일 목록 (None이면 Git diff 기반)
        output_file: 출력 파일 경로
    
    Returns:
        리뷰 결과
    """
    logger = StepLogger("코드리뷰 에이전트")
    logger.start()
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'commit': commit,
        'files_reviewed': 0,
        'total_issues': 0,
        'files': []
    }
    
    try:
        # 1. 리뷰할 파일 목록 결정
        logger.section("1. 리뷰할 파일 목록 결정")
        
        if files:
            review_files = files
            logger.info(f"지정된 파일: {len(review_files)}개")
        elif commit:
            # 특정 커밋의 변경사항
            commit_info = get_commit_info(commit)
            review_files = commit_info.get('files', [])
            logger.info(f"커밋 {commit[:8]}의 변경 파일: {len(review_files)}개")
            report['commit_info'] = commit_info
        elif is_git_repository():
            # 현재 변경사항
            changed_files = get_changed_files(staged=False)
            review_files = filter_code_files(changed_files)
            logger.info(f"현재 변경된 파일: {len(review_files)}개")
        else:
            logger.warning("Git 저장소가 아니거나 변경된 파일이 없습니다.")
            return report
        
        if not review_files:
            logger.warning("리뷰할 파일이 없습니다.")
            return report
        
        # 2. 각 파일 리뷰
        logger.section("2. 파일별 코드리뷰")
        
        for idx, file_path in enumerate(review_files, 1):
            logger.progress(idx, len(review_files), f"리뷰 중: {Path(file_path).name}")
            
            try:
                # 변경 전 코드 가져오기
                old_code = None
                if commit:
                    # 커밋의 변경 전 코드
                    import subprocess
                    project_root = PROJECT_ROOT
                    try:
                        result = subprocess.run(
                            ['git', 'show', f'{commit}^:{file_path}'],
                            cwd=project_root,
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        if result.returncode == 0:
                            old_code = result.stdout
                    except:
                        pass
                
                # 파일 리뷰
                review_result = review_file_changes(file_path, old_code=old_code)
                
                if review_result.get('review', {}).get('success'):
                    report['files'].append(review_result)
                    issues_count = len(review_result.get('review', {}).get('issues', []))
                    report['total_issues'] += issues_count
                    
                    if issues_count > 0:
                        logger.warning(f"  발견된 이슈: {issues_count}개")
                    else:
                        logger.success("  이슈 없음")
                else:
                    logger.warning(f"  리뷰 실패: {review_result.get('error', '알 수 없는 오류')}")
            
            except Exception as e:
                logger.warning(f"{file_path} 리뷰 실패: {str(e)}")
                continue
        
        report['files_reviewed'] = len(report['files'])
        
        # 3. 리포트 생성
        logger.section("3. 리포트 생성")
        
        if output_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = OUTPUT_DIR / f'review_report_{timestamp}.json'
        else:
            output_file = Path(output_file)
            output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.success(f"리포트 저장 완료: {output_file}")
        report['report_path'] = str(output_file)
        
        # 요약 출력
        logger.section("요약")
        logger.info(f"리뷰된 파일: {report['files_reviewed']}개")
        logger.info(f"발견된 이슈: {report['total_issues']}개")
        
        # 등급별 통계
        ratings = {}
        for file_result in report['files']:
            rating = file_result.get('review', {}).get('overall_rating', 'unknown')
            ratings[rating] = ratings.get(rating, 0) + 1
        
        if ratings:
            logger.info("등급별 통계:")
            for rating, count in ratings.items():
                logger.info(f"  {rating}: {count}개")
        
        return report
    
    except Exception as e:
        logger.error(f"에이전트 실행 실패: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        report['error'] = str(e)
        return report


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='코드리뷰 에이전트')
    parser.add_argument(
        '--commit',
        type=str,
        help='리뷰할 커밋 해시'
    )
    parser.add_argument(
        '--files',
        nargs='+',
        help='리뷰할 파일 목록'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='출력 파일 경로'
    )
    
    args = parser.parse_args()
    
    result = run_review_agent(
        commit=args.commit,
        files=args.files,
        output_file=args.output
    )
    
    if result.get('error'):
        sys.exit(1)


if __name__ == '__main__':
    main()

