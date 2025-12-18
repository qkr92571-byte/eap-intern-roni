# 일일 리포트 생성 워크플로우 가이드

이 가이드는 **메모리가 초기화된 상태**에서도 동일한 프로세스로 일일 리포트를 생성할 수 있도록 작성되었습니다.

## 📋 전체 워크플로우 개요

```
1. 나라장터 검색 및 수집
   ↓
2. GPT 검수 (적합/부적합 판정)
   ↓
3. 적합 공고 첨부파일 분석 및 서비스 항목 추출
   ↓
4. Firestore 업로드
   ↓
5. 슬랙 메시지 전송
```

---

## 🚀 빠른 시작 (전체 프로세스 한 번에 실행)

### 방법 1: 통합 스크립트 사용 (권장)

```bash
cd backend

# 1단계: 나라장터 검색 및 리포트 생성
python3 scripts/test_scraper.py

# 2단계: GPT 검수 (슬랙 전송 제외)
python3 scripts/run_review_cycle.py

# 3단계: 적합 공고 첨부파일 분석
python3 scripts/process_approved_announcements.py --date 2025-12-17

# 4단계: Firestore 업로드 (리포트 전체 동기화)
python3 scripts/sync_firestore_with_report.py

# 5단계: 슬랙 메시지 전송
python3 scripts/send_slack_report.py 251217
```

### 방법 2: WorkflowService 사용 (더 자동화)

```bash
cd backend

# 전체 워크플로우 자동 실행 (슬랙 전송 포함)
python3 scripts/review_and_upload_report.py --skip-slack --auto-upload
```

---

## 📝 단계별 상세 가이드

### 1단계: 나라장터 검색 및 수집

**목적**: 나라장터에서 키워드 기반 공고를 검색하고 리포트 파일 생성

**실행 명령**:
```bash
cd backend
python3 scripts/test_scraper.py
```

**결과물**:
- `backend/report/report_YYMMDD.json` - 수집된 공고 리스트
- `backend/history/history_YYMMDD.json` - 중복 체크용 공고번호 히스토리

**확인 사항**:
- 리포트 파일이 생성되었는지 확인
- 수집된 공고 개수가 0개가 아닌지 확인

**예상 소요 시간**: 5-10분 (키워드 개수에 따라 다름)

---

### 2단계: GPT 검수 (적합/부적합 판정)

**목적**: ChatGPT API를 사용하여 각 공고가 EAP에 적합한지 검수

**실행 명령**:
```bash
cd backend
python3 scripts/run_review_cycle.py
```

**결과물**:
- `backend/report/report_YYMMDD.json` 업데이트
  - 각 공고에 `reviewed: true`, `status: "approved" | "rejected"`, `review_result` 추가

**확인 사항**:
- 검수 완료 메시지 확인
- 적합/부적합 개수 확인
- 리포트 파일에 `reviewed`, `status` 필드가 추가되었는지 확인

**예상 소요 시간**: 공고 1개당 약 2-3초 (15개 공고 기준 약 30-45초)

**비용**: gpt-3.5-turbo 기준 공고 1개당 약 $0.002

---

### 3단계: 적합 공고 첨부파일 분석 및 서비스 항목 추출

**목적**: 적합 판정 받은 공고의 첨부파일을 다운로드하고 서비스 항목 추출

**실행 명령**:
```bash
cd backend
python3 scripts/process_approved_announcements.py --date 2025-12-17
```

**날짜 형식**: `YYYY-MM-DD` (예: `2025-12-17`)

**결과물**:
- `backend/report/report_YYMMDD.json` 업데이트
  - 적합 공고에 `service_items` 배열 추가
  - `service_items_extracted_at` 타임스탬프 추가
- `backend/downloads/YYYYMMDD/공고번호/` 디렉토리에 첨부파일 다운로드
- `backend/downloads/YYYYMMDD/공고번호/service_list_*.md` - 서비스 항목 마크다운

**확인 사항**:
- 적합 공고가 있는지 확인 (없으면 이 단계 건너뜀)
- 첨부파일 다운로드 성공 여부 확인
- 서비스 항목이 추출되었는지 확인

**예상 소요 시간**: 공고 1개당 약 1-2분 (첨부파일 크기에 따라 다름)

**주의사항**:
- 적합 공고가 없으면 자동으로 건너뜀
- 이미 `service_items`가 있는 공고는 건너뜀

---

### 4단계: Firestore 업로드

**목적**: 리포트 파일의 모든 공고를 Firestore에 업로드/동기화

**실행 명령**:
```bash
cd backend
python3 scripts/sync_firestore_with_report.py
```

**또는 특정 날짜 지정**:
```bash
python3 -c "
from datetime import datetime
from scripts.sync_firestore_with_report import sync_firestore_with_report
sync_firestore_with_report(datetime(2025, 12, 17))
"
```

**결과물**:
- Firestore `announcements` 컬렉션에 공고 문서 생성/업데이트
- 리포트에 없는 오늘 날짜 공고는 삭제 (동기화)

**확인 사항**:
- 업로드 성공 메시지 확인
- 추가/업데이트 개수 확인
- Firestore 콘솔에서 데이터 확인

**주의사항**:
- ⚠️ 이 스크립트는 리포트에 없는 오늘 날짜 공고를 삭제합니다
- 삭제를 원하지 않으면 `upload_report_to_firestore.py` 사용

**대안 (삭제 없이 업로드만)**:
```bash
python3 scripts/upload_report_to_firestore.py
```

---

### 5단계: 슬랙 메시지 전송

**목적**: 일일 리포트를 슬랙 채널에 전송

**실행 명령**:
```bash
cd backend
python3 scripts/send_slack_report.py 251217
```

**날짜 형식**: `YYMMDD` (예: `251217` = 2025-12-17)

**결과물**:
- 슬랙 채널 `C034EQD6W4W`에 리포트 메시지 전송
- `backend/report/report_YYMMDD.json`에 `slack_sent: true` 추가

**확인 사항**:
- 슬랙 채널에서 메시지 확인
- 리포트 파일에 `slack_sent` 필드 확인

**주의사항**:
- 이미 전송된 리포트는 중복 전송 방지
- 환경 변수 `SLACK_BOT_TOKEN`, `SLACK_CHANNEL_ID` 설정 필요

---

## 🔄 일일 리포트 생성 체크리스트

매일 아침 다음 순서로 실행하세요:

- [ ] **1단계**: `python3 scripts/test_scraper.py` 실행
  - 리포트 파일 생성 확인: `backend/report/report_YYMMDD.json`
  
- [ ] **2단계**: `python3 scripts/run_review_cycle.py` 실행
  - 검수 완료 확인: 적합/부적합 개수 확인
  
- [ ] **3단계**: `python3 scripts/process_approved_announcements.py --date YYYY-MM-DD` 실행
  - 적합 공고가 있으면 실행, 없으면 건너뜀
  
- [ ] **4단계**: `python3 scripts/sync_firestore_with_report.py` 실행
  - Firestore 업로드 확인
  
- [ ] **5단계**: `python3 scripts/send_slack_report.py YYMMDD` 실행
  - 슬랙 메시지 전송 확인

---

## 🛠️ 문제 해결

### 리포트 파일이 생성되지 않음

**원인**: 나라장터 사이트 구조 변경 또는 네트워크 오류

**해결**:
1. `backend/services/scraper_service.py`의 xpath 확인
2. 나라장터 사이트 접속 가능 여부 확인
3. Playwright 브라우저 재설치: `playwright install chromium`

---

### GPT 검수 실패

**원인**: OpenAI API 키 미설정 또는 API 오류

**해결**:
1. `.env` 파일에 `OPENAI_API_KEY` 확인
2. API 키 유효성 확인: https://platform.openai.com/api-keys
3. API 사용량/크레딧 확인

---

### Firestore 업로드 실패

**원인**: Firebase 키 파일 경로 오류 또는 권한 문제

**해결**:
1. `.env` 파일의 `FIREBASE_CREDENTIALS_PATH` 확인
2. 키 파일이 `backend/config/` 디렉토리에 있는지 확인
3. Firebase 콘솔에서 서비스 계정 권한 확인

---

### 슬랙 메시지 전송 실패

**원인**: Slack Bot Token 미설정 또는 채널 권한 문제

**해결**:
1. `.env` 파일에 `SLACK_BOT_TOKEN`, `SLACK_CHANNEL_ID` 확인
2. Slack 앱에 채널 권한이 있는지 확인
3. Bot이 채널에 초대되었는지 확인

---

## 📊 리포트 파일 구조

`backend/report/report_YYMMDD.json` 파일은 다음과 같은 구조를 가집니다:

```json
[
  {
    "announcement_number": "R25BK01235549-000",
    "title": "2026년 오송재단 근로자 지원 프로그램",
    "agency": "오송첨단의료산업진흥재단",
    "publish_date": "2025/12/17",
    "budget_amount": 58410000,
    "estimated_price": 53100000,
    "business_type": "일반용역",
    "created_at": "2025-12-17T16:50:37.862535",
    "source": "나라장터",
    "service_items": [
      {
        "구분": "1:1 심리상담",
        "설명": "대면 및 온라인으로 제공되는 개인 심리상담 서비스"
      }
    ],
    "service_items_extracted_at": "2025-12-17T16:56:33.911919",
    "display_status": 20,
    "reviewed": true,
    "review_result": "- 적합 여부: 적합\n- 이유: ...",
    "review_model": "gpt-3.5-turbo",
    "reviewed_at": "2025-12-17T16:56:00.491834",
    "status": "approved"
  }
]
```

---

## 🔗 관련 문서

- [SETUP.md](./SETUP.md) - 초기 설정 가이드
- [backend/scripts/README.md](./backend/scripts/README.md) - 스크립트 상세 가이드
- [FIREBASE_SETUP.md](./FIREBASE_SETUP.md) - Firebase 설정 가이드

---

## 💡 팁

1. **자동화**: Cron이나 스케줄러를 사용하여 매일 자동 실행 가능
2. **에러 로그**: 각 스크립트 실행 시 콘솔 출력을 파일로 저장하여 추적 가능
3. **테스트**: 새로운 환경에서는 먼저 `test_scraper.py`로 스크래퍼 동작 확인
4. **비용 관리**: GPT 검수는 비용이 발생하므로 공고 개수 확인 후 실행

