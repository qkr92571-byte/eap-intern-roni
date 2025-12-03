#!/usr/bin/env python3
"""
슬랙 리포트 전송 스크립트

오늘 수집된 리포트를 슬랙으로 전송합니다.
"""

import sys
import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트를 Python 경로에 추가 (backend 디렉토리)
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

# .env 파일 로드
env_path = Path(backend_dir) / '.env'
if env_path.exists():
    load_dotenv(env_path)
else:
    # 상위 디렉토리에서도 시도
    load_dotenv()

from services.slack_service import send_daily_report_to_slack

if __name__ == "__main__":
    print("=" * 60)
    print("슬랙 리포트 전송")
    print("=" * 60)
    print()
    
    # 날짜 지정 (명령줄 인자로 받을 수 있음)
    if len(sys.argv) > 1:
        try:
            date_str = sys.argv[1]
            report_date = datetime.strptime(date_str, '%Y%m%d')
        except ValueError:
            print(f"❌ 날짜 형식이 올바르지 않습니다. YYYYMMDD 형식으로 입력해주세요.")
            sys.exit(1)
    else:
        report_date = datetime.now()
    
    print(f"날짜: {report_date.strftime('%Y-%m-%d')}")
    print()
    
    success = send_daily_report_to_slack(report_date)
    
    if success:
        print("\n✅ 슬랙 메시지 전송 완료!")
    else:
        print("\n❌ 슬랙 메시지 전송 실패!")
        print("\n환경변수 확인:")
        print("  - SLACK_BOT_TOKEN: Slack Bot Token")
        print("  - SLACK_CHANNEL_ID: Slack Channel ID")
        sys.exit(1)

