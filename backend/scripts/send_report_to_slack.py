"""
리포트를 슬랙으로 전송하는 인터랙티브 CLI

- 전송 전에 메시지 예시(프리뷰)를 콘솔에 출력
- 공식 채널/테스트 채널 중 선택하여 전송
"""

import argparse
import json
import os
import sys
from pathlib import Path

# 프로젝트 루트를 경로에 추가
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from services.slack_service import send_report_to_slack, _build_g2b_detail_url
from utils.constants import SLACK_PRODUCTION_CHANNEL_ID


def _resolve_report_path(report_arg: str | None) -> Path:
    report_dir = backend_dir / "report"
    if report_arg:
        p = Path(report_arg)
        if not p.is_absolute():
            p = (backend_dir / report_arg).resolve()
        return p

    # 기본값: 가장 최근 report_*.json
    candidates = sorted(report_dir.glob("report_*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
    if not candidates:
        return report_dir / "report_000000.json"
    return candidates[0]


def _extract_announcements(report_data):
    if isinstance(report_data, dict):
        return report_data.get("announcements", [])
    if isinstance(report_data, list):
        return report_data
    return []


def _format_date_from_filename(report_path: Path) -> str:
    date_str = report_path.stem.replace("report_", "")
    try:
        year = 2000 + int(date_str[:2])
        month = date_str[2:4]
        day = date_str[4:6]
        return f"{year}-{month}-{day}"
    except Exception:
        return ""


def print_preview(report_path: Path) -> dict:
    with open(report_path, "r", encoding="utf-8") as f:
        report_data = json.load(f)

    announcements = _extract_announcements(report_data)
    total = len(announcements)
    approved = [a for a in announcements if a.get("status") == "approved"]
    rejected = [a for a in announcements if a.get("status") == "rejected"]

    formatted_date = _format_date_from_filename(report_path) or "날짜 미상"
    usergroup_id = os.getenv("SLACK_EAP_USERGROUP", "S08SE5ZTPQD")
    usergroup_mention = f"<!subteam^{usergroup_id}|@eap파트>"
    frontend_url = os.getenv("FRONTEND_URL", "http://172.30.1.17:3000")

    print("=" * 60)
    print("슬랙 메시지 예시 (프리뷰)")
    print("=" * 60)
    print(f"리포트: {report_path}")
    print()
    print(f"📊 EAP 공고 리포트 - {formatted_date}")
    print()
    print(usergroup_mention)
    print()
    print("📅 *검색일자*")
    print(formatted_date)
    print()
    print("📋 *신규 공고*")
    print(f"총 {total}개")
    print(f"  • 적합: {len(approved)}개")
    print(f"  • 부적합: {len(rejected)}개")
    print()
    print("✅ *적합 공고*")
    if not approved:
        print("적합 공고 없음")
    else:
        for i, ann in enumerate(approved, 1):
            title = ann.get("title", "제목 없음")
            ann_no = ann.get("announcement_number", "")
            link = _build_g2b_detail_url(ann_no)
            if link:
                print(f"{i}. <{link}|{title}>")
            else:
                print(f"{i}. {title} ({ann_no})")
    print()
    print("*전체 리포트*")
    print(f"<{frontend_url}|프론트엔드에서 보기>")
    print()

    meta = {}
    if isinstance(report_data, dict):
        meta = {
            "slack_sent": bool(report_data.get("slack_sent", False)),
            "slack_channel": report_data.get("slack_channel"),
            "slack_sent_at": report_data.get("slack_sent_at"),
        }
    return meta


def choose_channel() -> str | None:
    official_channel = os.getenv("SLACK_OFFICIAL_CHANNEL_ID", SLACK_PRODUCTION_CHANNEL_ID)
    test_channel = os.getenv("SLACK_TEST_CHANNEL_ID") or os.getenv("SLACK_CHANNEL_ID")
    print("=" * 60)
    print("전송 채널 선택")
    print("=" * 60)
    print(f"1) 공식 채널(SLACK_OFFICIAL_CHANNEL_ID): {official_channel}")
    print(f"2) 테스트 채널(SLACK_TEST_CHANNEL_ID/SLACK_CHANNEL_ID): {test_channel or '(미설정)'}")
    print("3) 취소")
    print()
    choice = input("선택 (1/2/3): ").strip()
    if choice == "1":
        return official_channel
    if choice == "2":
        return test_channel
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="슬랙 전송 인터랙티브 CLI")
    parser.add_argument("--report", type=str, help="리포트 경로 (예: report/report_260306.json)")
    args = parser.parse_args()

    report_path = _resolve_report_path(args.report)
    if not report_path.exists():
        print(f"❌ 리포트 파일을 찾을 수 없습니다: {report_path}")
        return 1

    meta = print_preview(report_path)
    if meta.get("slack_sent"):
        print("⚠️  이 리포트는 이전에 전송된 기록이 있습니다.")
        print(f"   slack_channel: {meta.get('slack_channel')}")
        print(f"   slack_sent_at: {meta.get('slack_sent_at')}")
        print()

    channel_id = choose_channel()
    if not channel_id:
        print("전송을 취소했습니다.")
        return 0

    print("=" * 60)
    print("슬랙 메시지 전송")
    print("=" * 60)
    print(f"리포트 파일: {report_path}")
    print(f"채널 ID: {channel_id}")
    print()

    result = send_report_to_slack(report_file=str(report_path), channel_id=channel_id)
    if result:
        print("\n✅ 슬랙 메시지 전송 완료!")
        return 0
    print("\n❌ 슬랙 메시지 전송 실패")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
