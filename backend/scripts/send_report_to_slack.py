"""
리포트를 슬랙 공식 채널로 전송하는 스크립트
"""

import sys
from pathlib import Path

# 프로젝트 루트를 경로에 추가
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from services.slack_service import send_report_to_slack
from utils.constants import SLACK_PRODUCTION_CHANNEL_ID

def main():
    # 리포트 파일 경로
    report_file = backend_dir / 'report' / 'report_260211.json'
    
    if not report_file.exists():
        print(f"❌ 리포트 파일을 찾을 수 없습니다: {report_file}")
        sys.exit(1)
    
    print("=" * 60)
    print("슬랙 메시지 전송")
    print("=" * 60)
    print(f"리포트 파일: {report_file}")
    print(f"채널 ID: {SLACK_PRODUCTION_CHANNEL_ID}")
    print()
    
    # 슬랙 메시지 전송
    result = send_report_to_slack(
        report_file=str(report_file),
        channel_id=SLACK_PRODUCTION_CHANNEL_ID
    )
    
    if result:
        print("\n✅ 슬랙 메시지 전송 완료!")
        return 0
    else:
        print("\n❌ 슬랙 메시지 전송 실패")
        return 1

if __name__ == '__main__':
    sys.exit(main())
