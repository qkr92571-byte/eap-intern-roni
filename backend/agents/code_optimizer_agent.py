"""
코드 최적화 에이전트
- 코드베이스 스캔 및 분석
- Linter 실행 및 결과 수집
- 코드 메트릭 수집
- AI 최적화 분석
- 안전한 변경사항 자동 적용
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

from services.linter_service import lint_directory, aggregate_linter_results
from services.code_analysis_service import analyze_directory, aggregate_metrics
from services.optimization_service import (
    analyze_code_for_optimization,
    identify_auto_fixable_issues,
    apply_optimization
)
from utils.code_safety_checker import validate_change, RiskLevel
from utils.logger import StepLogger

load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent.parent
OUTPUT_DIR = PROJECT_ROOT / 'backend' / 'code_analysis' / 'optimization_reports'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def scan_codebase(target_dirs: Optional[List[str]] = None) -> List[str]:
    """
    코드베이스 스캔
    
    Args:
        target_dirs: 분석할 디렉토리 목록 (None이면 전체)
    
    Returns:
        코드 파일 경로 리스트
    """
    if target_dirs is None:
        target_dirs = ['backend', 'frontend']
    
    code_files = []
    
    for target_dir in target_dirs:
        target_path = PROJECT_ROOT / target_dir
        if target_path.exists():
            # Python 파일
            for py_file in target_path.rglob('*.py'):
                rel_path = str(py_file.relative_to(PROJECT_ROOT))
                # 제외할 파일/디렉토리
                if not any(excluded in rel_path for excluded in [
                    '__pycache__', '.venv', 'venv', 'node_modules',
                    'build', 'dist', 'downloads', 'history', 'report'
                ]):
                    code_files.append(rel_path)
            
            # TypeScript/JavaScript 파일
            for ext in ['*.ts', '*.tsx', '*.js', '*.jsx']:
                for js_file in target_path.rglob(ext):
                    rel_path = str(js_file.relative_to(PROJECT_ROOT))
                    if 'node_modules' not in rel_path:
                        code_files.append(rel_path)
    
    return code_files


def run_optimization_agent(
    target_dirs: Optional[List[str]] = None,
    auto_fix: bool = False,
    output_file: Optional[str] = None
) -> Dict:
    """
    최적화 에이전트 실행
    
    Args:
        target_dirs: 분석할 디렉토리 목록
        auto_fix: 자동 수정 여부
        output_file: 출력 파일 경로
    
    Returns:
        최적화 결과
    """
    logger = StepLogger("코드 최적화 에이전트")
    logger.start()
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'target_dirs': target_dirs or ['backend', 'frontend'],
        'auto_fix': auto_fix,
        'files_analyzed': 0,
        'files_optimized': 0,
        'issues_found': 0,
        'issues_fixed': 0,
        'files': []
    }
    
    try:
        # 1. 코드베이스 스캔
        logger.section("1. 코드베이스 스캔")
        code_files = scan_codebase(target_dirs)
        logger.info(f"발견된 코드 파일: {len(code_files)}개")
        report['files_analyzed'] = len(code_files)
        
        if not code_files:
            logger.warning("분석할 파일이 없습니다.")
            return report
        
        # 2. Linter 실행
        logger.section("2. Linter 실행")
        linter_results = {}
        for target_dir in (target_dirs or ['backend', 'frontend']):
            logger.info(f"{target_dir} 디렉토리 Linter 실행 중...")
            dir_results = lint_directory(target_dir, recursive=True)
            linter_results.update(dir_results)
        
        linter_summary = aggregate_linter_results(linter_results)
        logger.info(f"Linter 이슈: {linter_summary['total_issues']}개")
        report['linter_summary'] = linter_summary
        
        # 3. 코드 분석
        logger.section("3. 코드 분석")
        code_analyses = {}
        for target_dir in (target_dirs or ['backend', 'frontend']):
            logger.info(f"{target_dir} 디렉토리 코드 분석 중...")
            dir_analyses = analyze_directory(target_dir, recursive=True)
            code_analyses.update(dir_analyses)
        
        metrics_summary = aggregate_metrics(code_analyses)
        logger.info(f"총 라인 수: {metrics_summary['total_lines']}")
        logger.info(f"총 함수 수: {metrics_summary['total_functions']}")
        report['code_metrics'] = metrics_summary
        
        # 4. AI 최적화 분석 (샘플 파일만)
        logger.section("4. AI 최적화 분석")
        logger.info("주요 파일에 대해 AI 최적화 분석을 수행합니다...")
        
        # 주요 파일 선택 (서비스 파일 우선)
        priority_files = [
            f for f in code_files 
            if 'service' in f or 'route' in f or 'utils' in f
        ][:10]  # 최대 10개만
        
        if not priority_files:
            priority_files = code_files[:10]
        
        optimization_results = []
        auto_fixable_issues = []
        
        for idx, file_path in enumerate(priority_files, 1):
            logger.progress(idx, len(priority_files), f"분석 중: {Path(file_path).name}")
            
            try:
                result = analyze_code_for_optimization(file_path)
                if result.get('success'):
                    optimization_results.append(result)
                    
                    # 자동 수정 가능한 이슈 식별
                    opt_result = result.get('optimization', {})
                    if opt_result.get('success'):
                        issues = opt_result.get('issues', [])
                        for issue in issues:
                            if issue.get('auto_fixable', False):
                                # 안전성 검사
                                validation = validate_change(
                                    file_path=file_path,
                                    change_type=issue.get('type', 'refactoring'),
                                    change_description=issue.get('message', '')
                                )
                                
                                if validation['risk_level'] == RiskLevel.SAFE.value:
                                    auto_fixable_issues.append({
                                        'file': file_path,
                                        'issue': issue,
                                        'validation': validation
                                    })
            except Exception as e:
                logger.warning(f"{file_path} 분석 실패: {str(e)}")
                continue
        
        report['optimization_results'] = optimization_results
        report['auto_fixable_issues'] = auto_fixable_issues
        report['issues_found'] = sum(
            len(r.get('optimization', {}).get('issues', []))
            for r in optimization_results
        )
        
        # 5. 자동 수정 적용
        if auto_fix and auto_fixable_issues:
            logger.section("5. 자동 수정 적용")
            logger.info(f"자동 수정 가능한 이슈: {len(auto_fixable_issues)}개")
            
            fixed_count = 0
            for fix_item in auto_fixable_issues:
                file_path = fix_item['file']
                issue = fix_item['issue']
                
                try:
                    result = apply_optimization(file_path, issue, backup=True)
                    if result.get('success'):
                        fixed_count += 1
                        logger.success(f"수정 완료: {Path(file_path).name}")
                    else:
                        logger.warning(f"수정 실패: {Path(file_path).name} - {result.get('error')}")
                except Exception as e:
                    logger.warning(f"수정 실패: {Path(file_path).name} - {str(e)}")
            
            report['issues_fixed'] = fixed_count
            report['files_optimized'] = fixed_count
        
        # 6. 리포트 생성
        logger.section("6. 리포트 생성")
        
        if output_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = OUTPUT_DIR / f'optimization_report_{timestamp}.json'
        else:
            output_file = Path(output_file)
            output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.success(f"리포트 저장 완료: {output_file}")
        report['report_path'] = str(output_file)
        
        # 요약 출력
        logger.section("요약")
        logger.info(f"분석된 파일: {report['files_analyzed']}개")
        logger.info(f"발견된 이슈: {report['issues_found']}개")
        if auto_fix:
            logger.info(f"수정된 이슈: {report['issues_fixed']}개")
        
        return report
    
    except Exception as e:
        logger.error(f"에이전트 실행 실패: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        report['error'] = str(e)
        return report


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='코드 최적화 에이전트')
    parser.add_argument(
        '--target-dir',
        action='append',
        help='분석할 디렉토리 (여러 번 지정 가능)'
    )
    parser.add_argument(
        '--auto-fix',
        action='store_true',
        help='자동 수정 활성화'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='출력 파일 경로'
    )
    
    args = parser.parse_args()
    
    target_dirs = args.target_dir if args.target_dir else None
    
    result = run_optimization_agent(
        target_dirs=target_dirs,
        auto_fix=args.auto_fix,
        output_file=args.output
    )
    
    if result.get('error'):
        sys.exit(1)


if __name__ == '__main__':
    main()

