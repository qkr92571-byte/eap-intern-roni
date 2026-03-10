PYTHON ?= python3

# 오늘자(KST 기준) 일일 리포트 생성
# - 수집 → 검수 → Firestore 업서트 → Slack 전송
# - 마지막에 Slack 전송 채널(공식/테스트/건너뛰기) 선택 프롬프트가 표시됩니다.
daily:
	$(PYTHON) -m backend.entrypoints.daily_report

# 자동 모드 (컨펌 없이 실행, 스케줄/CI용)
# - Slack 전송은 생략
daily-auto:
	$(PYTHON) -m backend.entrypoints.daily_report --skip-slack --auto

