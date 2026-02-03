PYTHON ?= python3

# 오늘자(KST 기준) 일일 리포트 생성
# - 수집 → 검수 → Firestore 업서트
# - Slack 전송은 생략 (--skip-slack)
daily:
	$(PYTHON) -m backend.entrypoints.daily_report --skip-slack --auto

