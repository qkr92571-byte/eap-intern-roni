# 나라장터 사업 공고 수집 시스템

나라장터 사업 공고를 **자동으로 수집·검수·업로드**하고, 필요 시 Slack으로 리포트를 전송하는 시스템입니다.  
수집/검수/업로드/알림 단계는 **멀티 에이전트 + 오케스트레이터** 구조로 구성되어 있습니다.

---

## 기술 스택

- **프론트엔드**: React + TypeScript (포트 3000)
- **백엔드**: Python + Flask
- **데이터베이스**: Firebase Firestore (NoSQL)
- **웹 스크래핑**: Playwright
- **스케줄러**: APScheduler / Cron (예정)
- **AI 검수**: OpenAI ChatGPT API

---

## 프로젝트 구조 (요약)

```text
eap-intern-roni/
├── frontend/                  # React + TypeScript 프론트엔드
│   ├── src/
│   │   ├── components/        # 공통 컴포넌트
│   │   ├── pages/             # 페이지 컴포넌트
│   │   └── services/          # API 서비스
│   └── package.json
│
├── backend/                   # 백엔드 및 배치/에이전트 로직
│   ├── app.py                 # Flask 앱 진입점
│   ├── requirements.txt       # 백엔드 의존성
│   │
│   ├── entrypoints/           # CLI/배치 진입점
│   │   └── daily_report.py    # 일일 리포트 생성 단일 진입점
│   │
│   ├── orchestration/         # 오케스트레이션 레이어
│   │   ├── orchestrator.py    # Orchestrator (멀티 에이전트 워크플로우)
│   │   └── policies.py        # 컨펌/정책 정의
│   │
│   ├── agents/                # 에이전트 레이어
│   │   ├── collector_agent.py # 수집 에이전트 (Collector)
│   │   ├── reviewer_agent.py  # 검수 에이전트 (Reviewer)
│   │   ├── reporter_agent.py  # 업로드/서비스 항목 에이전트 (Reporter)
│   │   └── notifier_agent.py  # Slack 알림 에이전트 (Notifier)
│   │
│   ├── skills/                # 에이전트가 호출하는 스킬 (작업 단위)
│   │   ├── scrape.py          # 나라장터 공고 수집
│   │   ├── review.py          # ChatGPT 검수
│   │   ├── firestore.py       # Firestore 업서트
│   │   ├── service_items.py   # 서비스 항목 수집
│   │   └── slack.py           # Slack 전송
│   │
│   ├── services/              # 도메인 서비스 (재사용 가능한 비즈니스 로직)
│   │   ├── scraper_service.py   # Playwright 스크래퍼
│   │   ├── review_service.py    # 리포트 검수 서비스
│   │   ├── firebase_service.py  # Firebase/Firebase Admin 연동
│   │   ├── slack_service.py     # Slack 블록 메시지 전송
│   │   └── file_service.py      # report/history/duplicate_reports 관리
│   │
│   ├── report/                # 날짜별 수집/검수 리포트 (report_YYMMDD.json)
│   ├── history/               # 날짜별 수집 공고번호 히스토리 (history_YYMMDD.json)
│   ├── duplicate_reports/     # 신규 없음 + 중복만 있는 날의 중복 리포트
│   ├── downloads/             # 스크래핑 중 다운로드된 파일
│   ├── config/                # Firebase 등 설정 파일 (서비스 계정 키 포함)
│   ├── prompts/               # EAP 검수 프롬프트 등
│   └── utils/                 # 공통 유틸리티 (OpenAI 클라이언트, 로거 등)
│
├── Makefile                   # 백엔드 편의 명령어 (make daily 등)
├── CLAUDE.md                  # AI(Claude Code) 개발 규칙
├── FIREBASE_SETUP.md          # Firebase 초기 설정 가이드
├── SCHEMA_DOCUMENTATION.md    # Firestore 데이터 스키마 명세
└── README.md
```

---

## 빠른 시작

### 1) 참고 문서

- **[FIREBASE_SETUP.md](./FIREBASE_SETUP.md)** – Firebase 서비스 계정 키 및 Firestore 초기 설정
- **[SCHEMA_DOCUMENTATION.md](./SCHEMA_DOCUMENTATION.md)** – Firestore 데이터 스키마 명세
- **[CLAUDE.md](./CLAUDE.md)** – AI(Claude Code) 개발 규칙 및 운영 가이드

---

### 2) 백엔드 설정

```bash
cd backend

# 가상환경 생성
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# Playwright 브라우저 설치
playwright install chromium
```

#### `.env` (backend/.env) 예시

```env
# Firebase
FIREBASE_CREDENTIALS_PATH=config/firebase-credentials.json

# OpenAI
OPENAI_API_KEY=sk-...

# Slack (선택, Slack 알림 기능 사용 시)
SLACK_BOT_TOKEN=xoxb-...
SLACK_OFFICIAL_CHANNEL_ID=C034EQD6W4W
SLACK_TEST_CHANNEL_ID=C071ZL69JQZ
SLACK_EAP_USERGROUP=S08SE5ZTPQD

# 프론트엔드 URL (Slack 메시지 링크용)
FRONTEND_URL=https://eap-intern-roni.web.app

# 기타 설정 (필요 시)
# SKIP_FIRESTORE_PROMPT=true  # Firestore에서 프롬프트를 가져오지 않고 로컬 파일 사용
```

> `FIREBASE_CREDENTIALS_PATH`는 **backend 디렉터리 기준 상대 경로**입니다.  
> 예: `backend/config/firebase-credentials.json`

---

### 3) 프론트엔드 설정

```bash
cd frontend
npm install
npm start
```

- 프론트엔드는 기본적으로 `http://localhost:3000`에서 실행됩니다.

---

## 일일 리포트 생성 (멀티 에이전트 워크플로우)

### 1) 가장 쉬운 방법: `make daily`

프로젝트 루트에서:

```bash
make daily
```

- 내부적으로 실행되는 것:
  - `python3 -m backend.entrypoints.daily_report --skip-slack --auto`
- 수행 흐름:
  1. **수집** – `CollectorAgent` → `skill_scrape_g2b` → `scraper_service.run_scraper`
  2. **검수 (GPT)** – `ReviewerAgent` → `skill_review_announcements` → `review_service.review_report_file`
  3. **서비스 항목 수집** – `ReporterAgent.collect_service_items` (실패해도 워크플로우는 계속)
  4. **Firestore 업서트** – `ReporterAgent.upload_to_firestore` → `skill_upsert_firestore`
  5. **Slack 전송** – `NotifierAgent.send_report` (기본적으로 `--skip-slack`인 경우 실행 안 함)

> `--auto` 모드는 중간 컨펌 없이 자동으로 진행되며, Slack은 기본적으로 전송하지 않습니다.

### 2) 직접 엔트리포인트 실행

```bash
# 오늘자(KST 기준) 리포트 생성 (슬랙 제외)
python3 -m backend.entrypoints.daily_report --skip-slack --auto

# 특정 날짜 리포트 생성
python3 -m backend.entrypoints.daily_report --date 2026-02-03 --skip-slack --auto
```

지원 옵션:

- `--date YYYY-MM-DD`: 특정 날짜 기준 리포트
- `--skip-review`: GPT 검수 생략
- `--skip-service-items`: 서비스 항목 수집 생략
- `--skip-slack`: Slack 전송 생략
- `--auto`: 자동 모드 (컨펌 없이 진행)

---

## 리포트 / 히스토리 / 중복 리포트

- **리포트 파일**: `backend/report/report_YYMMDD.json`
  - 수집 및 검수 결과가 반영된 공고 리스트
  - 구조: 리스트 또는 `{ "announcements": [...], "slack_sent": ... }` 형태 (Slack 중복 방지용)

- **히스토리 파일**: `backend/history/history_YYMMDD.json`
  - 해당 날짜에 수집된 공고번호 목록 (중복 체크용)

- **중복 리포트 파일**: `backend/duplicate_reports/duplicate_report_YYMMDD.json`
  - "오늘 수집된 공고가 모두 과거 히스토리에 존재(신규 없음, 중복만 있는 날)"인 경우 생성
  - 구조:
    ```json
    {
      "date": "2026-02-03",
      "generated_at": "2026-02-03T12:34:56+09:00",
      "total_duplicates": 10,
      "announcements": [ ... 중복 공고들 ... ]
    }
    ```

---

## 주요 기능 요약

1. **나라장터 사업 공고 자동 수집**
   - Playwright 기반 스크래핑
   - 키워드 기반 검색
   - 업무구분, 게시일, 예산 등 필터링
   - 과거 히스토리 기준 중복 제거

2. **AI 기반 스마트 검수**
   - 제외 키워드 자동 필터링 (콜센터, 차량 임차 등)
   - OpenAI ChatGPT를 이용한 적합/부적합 검수
   - 검수 결과 및 사유를 리포트 파일에 저장

3. **Firestore 업서트**
   - `announcement_number` 기준 upsert
   - 신규/업데이트/건너뜀/실패 건수 집계
   - `display_status` 등 운영 필드 기본값 설정

4. **Slack 리포트 전송 (선택)**
   - EAP 파트 유저그룹 멘션 포함
   - 적합/부적합/미검수 통계
   - 프론트엔드 리포트 링크 포함
   - 전송은 **항상 사전 컨펌 후** 수행

---

## API 엔드포인트 (Flask)

> 프론트엔드/운영에서 사용하는 REST API는 기존 구조를 유지합니다.

- `GET /api/announcements` – 공고 목록 조회
- `GET /api/announcements/:id` – 공고 상세 조회
- `POST /api/announcements/scrape` – 공고 수집 실행
- `POST /api/announcements/filter` – 공고 필터링 및 검수
- `PUT /api/announcements/:id` – 공고 업데이트
- `DELETE /api/announcements/:id` – 공고 삭제

구체적인 파라미터 및 응답 형식은 `routes/announcement_routes.py` 및 관련 서비스 코드를 참고하세요.

---

## 주의사항 및 운영 팁

1. **나라장터 사이트 구조 변경 대응**
   - `backend/services/scraper_service.py`의 selector/xpath는 사이트 구조 변경 시 업데이트가 필요합니다.
   - 관련 주석을 참고하여 수정하세요.

2. **Firebase 설정**
   - 서비스 계정 키는 `backend/config/` 아래에 두고,
   - `backend/.env`의 `FIREBASE_CREDENTIALS_PATH` 경로를 반드시 확인하세요.

3. **OpenAI 비용/키 관리**
   - `OPENAI_API_KEY`는 필수이며, 검수 호출 시 비용이 발생합니다.
   - 운영 환경에서는 `--skip-review` 옵션 등으로 호출 빈도를 조절할 수 있습니다.

4. **Slack 전송 정책**
   - 규칙 상, "채팅/콘솔에서 명시적으로 승인된 경우"에만 Slack 전송을 수행해야 합니다.
   - 텍스트-only 메시지가 아니라, 정의된 블록 템플릿을 사용해야 합니다.

5. **법적/윤리적 고려**
   - 웹 스크래핑 시 나라장터 이용약관을 준수해야 합니다.
   - 수집 데이터에 개인정보가 포함될 가능성이 있는 경우, 별도의 마스킹/보존 정책이 필요합니다.

---

## 문의 / 유지보수

- **운영 규칙 및 워크플로우**: [CLAUDE.md](./CLAUDE.md) 참고
- **스키마/데이터 구조**: [SCHEMA_DOCUMENTATION.md](./SCHEMA_DOCUMENTATION.md) 참고
- **Firebase 초기 설정**: [FIREBASE_SETUP.md](./FIREBASE_SETUP.md) 참고
- 구조/설계 개선이 필요할 경우, Orchestrator 및 각 에이전트/스킬 레이어를 기준으로 변경 범위를 분리해서 작업하는 것을 권장합니다.