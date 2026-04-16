#!/usr/bin/env python3
"""
일일 리포트 생성 단일 진입점

사용법:
    python -m backend.entrypoints.daily_report [--date YYYY-MM-DD] [--skip-review] [--skip-service-items] [--skip-slack] [--auto]

예시:
    # 오늘자 리포트 생성 (대화형)
    python -m backend.entrypoints.daily_report
    
    # 특정 날짜 리포트 생성
    python -m backend.entrypoints.daily_report --date 2026-02-03
    
    # 자동 모드 (컨펌 없이 실행, 스케줄/CI용)
    python -m backend.entrypoints.daily_report --auto
    
    # 검수 건너뛰기
    python -m backend.entrypoints.daily_report --skip-review
    
    # 슬랙 전송 건너뛰기
    python -m backend.entrypoints.daily_report --skip-slack
"""

import argparse
import sys
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
import os
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from orchestration.orchestrator import Orchestrator
from orchestration.policies import ConfirmPolicy


def parse_args():
    """CLI 인자 파싱"""
    parser = argparse.ArgumentParser(
        description='일일 리포트 생성',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  # 오늘자 리포트 생성
  python -m backend.entrypoints.daily_report
  
  # 특정 날짜 리포트 생성
  python -m backend.entrypoints.daily_report --date 2026-02-03
  
  # 자동 모드 (컨펌 없이 실행)
  python -m backend.entrypoints.daily_report --auto
  
  # 검수 건너뛰기
  python -m backend.entrypoints.daily_report --skip-review
        """
    )
    
    parser.add_argument(
        '--date',
        type=str,
        help='리포트 날짜 (YYYY-MM-DD 형식, 기본값: 오늘 KST)'
    )
    
    parser.add_argument(
        '--skip-collect',
        action='store_true',
        help='수집 단계 건너뛰기 (기존 리포트 파일로 재검수 시 사용)'
    )

    parser.add_argument(
        '--skip-review',
        action='store_true',
        help='검수 단계 건너뛰기'
    )
    
    parser.add_argument(
        '--skip-service-items',
        action='store_true',
        help='서비스 항목 수집 건너뛰기'
    )
    
    parser.add_argument(
        '--skip-slack',
        action='store_true',
        help='슬랙 전송 건너뛰기'
    )
    
    parser.add_argument(
        '--auto',
        action='store_true',
        help='자동 모드 (컨펌 없이 실행, 스케줄/CI용)'
    )
    
    return parser.parse_args()


def main():
    """메인 함수"""
    args = parse_args()
    
    # 날짜 파싱
    report_date = None
    if args.date:
        try:
            report_date = datetime.strptime(args.date, '%Y-%m-%d')
        except ValueError:
            print(f"❌ 날짜 형식 오류: {args.date}")
            print("   올바른 형식: YYYY-MM-DD (예: 2026-02-03)")
            sys.exit(1)
    
    # 컨펌 정책 결정
    confirm_policy = ConfirmPolicy.AUTO.value if args.auto else ConfirmPolicy.INTERACTIVE.value
    
    # Orchestrator 생성
    orchestrator = Orchestrator(confirm_policy=confirm_policy)
    
    # 워크플로우 실행
    results = orchestrator.execute_daily_report(
        report_date=report_date,
        skip_collect=args.skip_collect,
        skip_review=args.skip_review,
        skip_service_items=args.skip_service_items,
        skip_slack=args.skip_slack
    )
    
    # 결과에 따라 종료 코드 설정
    if results.get('success'):
        sys.exit(0)
    else:
        print(f"\n❌ 워크플로우 실패: {results.get('error')}")
        sys.exit(1)


if __name__ == '__main__':
    main()
