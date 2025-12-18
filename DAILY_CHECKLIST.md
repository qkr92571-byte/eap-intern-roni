# 일일 리포트 생성 체크리스트

매일 아침 이 체크리스트를 따라 일일 리포트를 생성하세요.

---

## 📋 체크리스트

### ✅ 1단계: 나라장터 검색 및 수집

```bash
cd backend
python3 scripts/test_scraper.py
```

**확인 사항**:
- [ ] 리포트 파일 생성 확인: `backend/report/report_YYMMDD.json`
- [ ] 수집된 공고 개수가 0개가 아닌지 확인
- [ ] 에러 메시지가 없는지 확인

**예상 소요 시간**: 5-10분

---

### ✅ 2단계: GPT 검수

```bash
python3 scripts/run_review_cycle.py
```

**확인 사항**:
- [ ] 검수 완료 메시지 확인
- [ ] 적합/부적합 개수 확인
- [ ] 리포트 파일에 `reviewed`, `status` 필드 추가 확인

**예상 소요 시간**: 공고 1개당 약 2-3초

---

### ✅ 3단계: 적합 공고 첨부파일 분석

**주의**: 적합 공고가 있는 경우에만 실행

```bash
python3 scripts/process_approved_announcements.py --date $(date +%Y-%m-%d)
```

**확인 사항**:
- [ ] 적합 공고가 있는지 확인 (없으면 이 단계 건너뜀)
- [ ] 첨부파일 다운로드 성공 여부 확인
- [ ] 서비스 항목 추출 확인

**예상 소요 시간**: 공고 1개당 약 1-2분

---

### ✅ 4단계: Firestore 업로드

```bash
python3 scripts/sync_firestore_with_report.py
```

**확인 사항**:
- [ ] 업로드 성공 메시지 확인
- [ ] 추가/업데이트 개수 확인
- [ ] Firestore 콘솔에서 데이터 확인 (선택사항)

**예상 소요 시간**: 1-2분

---

### ✅ 5단계: 슬랙 메시지 전송 (선택사항)

```bash
python3 scripts/send_slack_report.py $(date +%y%m%d)
```

**확인 사항**:
- [ ] 슬랙 채널에서 메시지 확인
- [ ] 리포트 파일에 `slack_sent` 필드 확인

**예상 소요 시간**: 10-20초

---

## 🚀 한 번에 실행 (고급 사용자용)

전체 프로세스를 한 번에 실행하려면:

```bash
cd backend

# 1. 수집
python3 scripts/test_scraper.py && \
# 2. 검수
python3 scripts/run_review_cycle.py && \
# 3. 첨부파일 분석 (적합 공고가 있는 경우만)
python3 scripts/process_approved_announcements.py --date $(date +%Y-%m-%d) && \
# 4. Firestore 업로드
python3 scripts/sync_firestore_with_report.py && \
# 5. 슬랙 전송
python3 scripts/send_slack_report.py $(date +%y%m%d)
```

---

## 📊 결과 확인

### 리포트 파일 확인

```bash
# 오늘 날짜 리포트 확인
cat backend/report/report_$(date +%y%m%d).json | jq '. | length'

# 적합 공고 개수 확인
cat backend/report/report_$(date +%y%m%d).json | jq '[.[] | select(.status == "approved")] | length'
```

### Firestore 확인

1. Firebase 콘솔 접속: https://console.firebase.google.com
2. Firestore Database 탭
3. `announcements` 컬렉션 확인
4. 오늘 날짜 공고 확인

---

## ⚠️ 문제 발생 시

### 리포트 파일이 생성되지 않음

- 나라장터 사이트 접속 확인
- Playwright 브라우저 재설치: `playwright install chromium`
- `backend/services/scraper_service.py`의 xpath 확인

### GPT 검수 실패

- `.env` 파일의 `OPENAI_API_KEY` 확인
- API 키 유효성 확인: https://platform.openai.com/api-keys
- API 사용량/크레딧 확인

### Firestore 업로드 실패

- `.env` 파일의 `FIREBASE_CREDENTIALS_PATH` 확인
- 키 파일이 올바른 경로에 있는지 확인
- Firebase 콘솔에서 프로젝트 ID 확인

### 슬랙 메시지 전송 실패

- `.env` 파일의 `SLACK_BOT_TOKEN`, `SLACK_CHANNEL_ID` 확인
- Slack 앱에 채널 권한이 있는지 확인
- Bot이 채널에 초대되었는지 확인

---

## 📚 관련 문서

- [WORKFLOW_GUIDE.md](./WORKFLOW_GUIDE.md) - 상세 워크플로우 가이드
- [QUICK_START.md](./QUICK_START.md) - 빠른 시작 가이드

