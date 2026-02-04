# 스크립트 사용 가이드

이 디렉토리는 **에이전트/Orchestrator 기반 워크플로우의 하위 레벨 스크립트와 유틸리티**를 모아둔 곳입니다.

- **운영/일상 워크플로우의 표준 진입점**은 아래와 같습니다.
  - `make daily`
  - `python -m backend.entrypoints.daily_report --skip-slack --auto`
- 아래 스크립트들은 주로 **개별 단계 디버깅, 테스트, 유틸리티 목적**으로 사용하는 것을 권장합니다.

## 스크립트 분류

- **운영/지원 유틸리티 (안전)**
  - `test_firebase.py`, `test_db_insert.py`, `create_firestore_index.py`
  - `test_api.py`, `collect_monthly_data.py`, `collect_competitor_awards.py`, `upload_competitor_reports.py`, `simplify_competitor_report.py`
- **단계별 디버깅/수동 실행용 (주의)**
  - `test_scraper.py`, `run_review_cycle.py`, `process_approved_announcements.py`
  - `sync_firestore_with_report.py`, `upload_report_to_firestore.py`, `send_slack_report.py`
- **레거시 워크플로우 (멀티 에이전트로 대체됨, 가급적 사용 지양)**
  - `review_and_upload_report.py` (WorkflowService 기반 통합 스크립트)

아래 개별 항목 설명에서 각 스크립트의 구체적인 역할과 주의사항을 확인할 수 있습니다.

## 스크립트 목록

### 1. `test_scraper.py`
나라장터 스크래퍼 테스트

**사용법:**
```bash
cd backend
python scripts/test_scraper.py
```

**기능:**
- 오늘 날짜로 나라장터 공고 수집 테스트
- 리포트 및 히스토리 파일 생성 확인

---

### 2. `upload_report_to_firestore.py`
리포트 파일을 Firestore에 업로드

**사용법:**
```bash
cd backend
python scripts/upload_report_to_firestore.py
```

**기능:**
- 오늘 날짜의 리포트 파일을 Firestore에 업로드
- 중복 체크 후 저장
- 업로드 결과 통계 출력

---

### 3. `review_and_upload_report.py` ⚠️ **레거시 (멀티 에이전트로 대체됨)**
리포트 파일 검수 및 Firestore 업로드 통합 (이전 세대 워크플로우)

> 현재는 `backend/entrypoints/daily_report.py` + Orchestrator/Agents 구조가 **공식 표준**입니다.  
> 이 스크립트는 개별 단계 동작을 디버깅하거나, 과거 워크플로우를 재현해야 할 때만 사용하세요.

**대체 경로(권장):**
```bash
cd backend

# Orchestrator 기반 통합 실행
python -m backend.entrypoints.daily_report --skip-slack --auto
```

---

### 4. `delete_old_firestore_data.py`
오늘이 아닌 날짜의 Firestore 데이터 삭제

**사용법:**
```bash
cd backend
python scripts/delete_old_firestore_data.py
```

**기능:**
- `created_at`이 오늘이 아닌 데이터 조회
- 사용자 확인 후 삭제

**주의사항:**
- ⚠️ 데이터 삭제는 되돌릴 수 없습니다
- 삭제 전 반드시 확인하세요

---

### 5. `test_api.py`
API 엔드포인트 테스트

**사용법:**
```bash
cd backend
python scripts/test_api.py
```

**기능:**
- 백엔드 API 엔드포인트 테스트
- 응답 확인

---

### 6. `test_firebase.py`
Firebase 연결 테스트

**사용법:**
```bash
cd backend
python scripts/test_firebase.py
```

**기능:**
- Firebase 초기화 테스트
- Firestore 연결 확인

---

### 7. `test_db_insert.py`
Firestore 데이터 삽입 테스트

**사용법:**
```bash
cd backend
python scripts/test_db_insert.py
```

**기능:**
- 테스트 데이터를 Firestore에 삽입
- 데이터 구조 확인

---

### 8. `create_firestore_index.py`
Firestore 인덱스 생성

**사용법:**
```bash
cd backend
python scripts/create_firestore_index.py
```

**기능:**
- Firestore 쿼리 인덱스 생성
- `firestore.indexes.json` 파일 기반

---

## 통합 워크플로우 (레거시 스크립트 기반)

> 참고용입니다. 실제 운영에서는 Orchestrator 기반 일일 리포트 진입점을 사용하세요.  
> (예: `make daily`, `python -m backend.entrypoints.daily_report --skip-slack --auto`)

### 전체 프로세스 (수집 → 검수 → 업로드, 레거시)

```bash
# 1. 데이터 수집
cd backend
python scripts/test_scraper.py

# 2. 검수 및 업로드 (통합, 레거시)
python scripts/review_and_upload_report.py
```

또는 API를 통해 (레거시 엔드포인트 기준):

```bash
# 1. 데이터 수집
curl -X POST http://localhost:5001/api/announcements/scrape

# 2. 검수 및 업로드 (통합)
curl -X POST http://localhost:5001/api/reports/review-and-upload \
  -H "Content-Type: application/json" \
  -d '{}'
```

---

## 환경 변수 설정

`backend/.env` 파일에 다음 변수들이 설정되어 있어야 합니다:

```env
# Firebase 설정
FIREBASE_CREDENTIALS_PATH=config/eap-intern-roni-firebase-adminsdk-*.json
FIREBASE_PROJECT_ID=eap-intern-roni

# OpenAI API 설정 (검수 기능 사용 시 필수)
OPENAI_API_KEY=sk-...

# Flask 설정
PORT=5001
```

---

## 문제 해결

### OpenAI API 키 오류
```
⚠️  OPENAI_API_KEY가 설정되지 않았습니다.
```
**해결:** `.env` 파일에 `OPENAI_API_KEY`를 추가하세요.

### Firebase 초기화 오류
```
⚠️  Firebase 키 파일을 찾을 수 없습니다
```
**해결:** `FIREBASE_CREDENTIALS_PATH`가 올바른지 확인하세요.

### 리포트 파일 없음
```
⚠️  검수할 데이터가 없습니다.
```
**해결:** 먼저 `test_scraper.py`를 실행하여 리포트 파일을 생성하세요.
