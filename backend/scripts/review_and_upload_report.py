#!/usr/bin/env python3
"""
리포트 검수 및 Firestore 업로드 통합 스크립트

1. 리포트 파일을 ChatGPT API로 검수
2. 검수 결과를 리포트 파일에 반영
3. 검수된 리포트를 Firestore에 업로드

리팩토링: WorkflowService를 사용하여 단계별로 분리
"""

import sys
import os
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가 (backend 디렉토리)
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from services.workflow_service import WorkflowService


def review_and_upload_report(report_date=None, skip_slack=False, auto_upload=False):
    """
    리포트 검수 및 Firestore 업로드 통합 프로세스
    
    Args:
        report_date: 날짜 (기본값: 오늘)
        skip_slack: 슬랙 전송 건너뛰기 여부 (기본값: False)
        auto_upload: Firestore 업로드 자동 진행 여부 (기본값: False)
    """
    # WorkflowService를 사용하여 워크플로우 실행
    workflow = WorkflowService(report_date=report_date, auto_upload=auto_upload)
    result = workflow.run_full_workflow(skip_slack=skip_slack, confirm_before_review=False)
    
    if not result.get('success'):
        sys.exit(1)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='리포트 검수 및 Firestore 업로드')
    parser.add_argument(
        '--skip-slack',
        action='store_true',
        help='슬랙 메시지 전송 건너뛰기'
    )
    parser.add_argument(
        '--auto-upload',
        action='store_true',
        help='Firestore 업로드 자동 진행 (사용자 입력 없이)'
    )
    
    args = parser.parse_args()
    # 오늘 날짜로 검수 및 업로드
    # 기본적으로 슬랙 전송은 건너뛰기 (중복 방지)
    # 슬랙 전송이 필요하면 --skip-slack 플래그를 사용하지 않거나 별도로 전송
    review_and_upload_report(skip_slack=True, auto_upload=args.auto_upload)

