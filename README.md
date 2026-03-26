# 나라장터 사업 공고 수집 시스템

나라장터 사업 공고를 **자동으로 수집·검수·업로드**하고, 결과를 Slack으로 알리는 시스템입니다.
수집 → 검수 → 업로드 → 알림 단계는 **멀티 에이전트 + 오케스트레이터** 구조로 구성되어 있으며,
GitHub Actions로 매일 KST 17:00에 자동 실행됩니다.

- **프론트엔드 (Firebase Hosting)**: https://eap-intern-roni.web.app

---

## 기술 스택

| 구분 | 기술 |
|------|------|
| 프론트엔드 | React + TypeScript, Material-UI, Recharts |
| 백엔드 | Python, Flask |
| 데이터베이스 | Firebase Firestore (NoSQL) |
| 웹 스크래핑 | Playwright (Chromium) |
| AI 검수 | OpenAI ChatGPT API |
| 알림 | Slack Block Kit |
| CI/CD | GitHub Actions + VPN Gate (한국 IP 우회) |
| 프론트엔드 호스팅 | Firebase Hosting |

---

## 아키텍처

```
GitHub Actions (매일 KST 17:00)
        │
        ▼
  daily_report.py  ← 단일 진입점
        │
        ▼
  Orchestrator  ← 워크플로우 관리, 컨펌 정책
   ┌────┴──────────────────────────┐
   │                               │
CollectorAgent               ReviewerAgent
(나라장터 스크래핑)            (GPT 검수)
   │                               │
   └─────────────┬─────────────────┘
                 │
           ReporterAgent
       (Firestore 업서트 + 서비스 항목 수집)
                 │
           NotifierAgent
            (Slack 전송)
```

각 에이전트는 `skills/` 레이어의 함수를 호출하고, 스킬은 `services/` 레이어를 통해 외부 시스템과 통신합니다.

---

## 프로젝트 구조

```text
eap-intern-roni/
├── .github/
│   └── workflows/
│       └── daily-report.yml        # GitHub Actions 자동 실행 (KST 17:00 + VPN Gate)
│
├── frontend/                       # React + TypeScript 프론트엔드
│   └── src/
│       ├── pages/
│       │   ├── Home.tsx            # 대시보드 (통계, 차트, 최근 공고)
│       │   ├── AnnouncementList.tsx   # 공고 목록 (검색/정렬/필터/페이지네이션)
│       │   ├── AnnouncementDetail.tsx # 공고 상세
│       │   ├── CompetitorTrends.tsx   # 경쟁사 동향
│       │   └── Settings.tsx           # 설정
│       ├── hooks/                  # 데이터 페칭 훅
│       ├── services/api.ts         # Firestore 직접 조회
│       ├── components/             # 공통 컴포넌트
│       └── types/                  # TypeScript 타입 정의
│
├── backend/
│   ├── entrypoints/
│   │   └── daily_report.py         # CLI 진입점
│   │
│   ├── orchestration/
│   │   ├── orchestrator.py         # 멀티 에이전트 워크플로우 조율
│   │   └── policies.py             # 컨펌/자동 실행 정책
│   │
│   ├── agents/                     # 에이전트 레이어
│   │   ├── collector_agent.py      # 수집
│   │   ├── reviewer_agent.py       # 검수
│   │   ├── reporter_agent.py       # 업로드 + 서비스 항목
│   │   └── notifier_agent.py       # Slack 알림
│   │
│   ├── skills/                     # 에이전트가 호출하는 작업 단위
│   │   ├── scrape.py               # 나라장터 스크래핑
│   │   ├── review.py               # GPT 검수
│   │   ├── firestore.py            # Firestore 업서트
│   │   ├── service_items.py        # 서비스 항목 수집
│   │   └── slack.py                # Slack 전송
│   │
│   ├── services/                   # 외부 시스템 연동 서비스
│   │   ├── scraper_service.py      # Playwright 스크래퍼
│   │   ├── review_service.py       # ChatGPT 검수 로직
│   │   ├── firebase_service.py     # Firestore 연동
│   │   ├── slack_service.py        # Slack 블록 메시지 전송
│   │   └── file_service.py         # 리포트/히스토리 파일 관리
│   │
│   ├── report/                     # 날짜별 수집 리포트 (report_YYMMDD.json)
│   ├── history/                    # 수집 공고번호 히스토리 (중복 체크용)
│   ├── duplicate_reports/          # 신규 공고 없는 날의 중복 리포트
│   ├── config/                     # Firebase 서비스 계정 키 등
│   ├── prompts/                    # GPT 검수 프롬프트
│   └── utils/                      # 공통 유틸리티
│
├── Makefile                        # 편의 명령어
├── CLAUDE.md                       # AI(Claude Code) 개발 규칙
├── FIREBASE_SETUP.md               # Firebase 초기 설정 가이드
└── SCHEMA_DOCUMENTATION.md         # Firestore 데이터 스키마 명세
```

---

## 빠른 시작

### 1) 백엔드 설정

```bash
cd backend

# 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# Playwright 브라우저 설치
playwright install chromium
```

#### `backend/.env` 설정

```env
# Firebase
FIREBASE_CREDENTIALS_PATH=config/firebase-credentials.json

# OpenAI
OPENAI_API_KEY=sk-...

# Slack (알림 기능 사용 시)
SLACK_BOT_TOKEN=xoxb-...
SLACK_CHANNEL_ID=C034EQD6W4W         # 공식 채널
SLACK_EAP_USERGROUP=S08SE5ZTPQD      # EAP 파트 유저그룹

# 프론트엔드 URL (Slack 메시지 링크용)
FRONTEND_URL=https://eap-intern-roni.web.app
```

> `FIREBASE_CREDENTIALS_PATH`는 `backend/` 디렉터리 기준 상대 경로입니다.

### 2) 프론트엔드 설정

```bash
cd frontend
npm install
npm start
# http://localhost:3000 에서 실행
```

> 파일 감시 이슈(EMFILE 등) 발생 시:
> ```bash
> HOST=0.0.0.0 PORT=3000 CHOKIDAR_USEPOLLING=true WATCHPACK_POLLING=true npm start
> ```

---

## 일일 리포트 실행

### 가장 쉬운 방법: `make daily`

```bash
make daily        # 대화형 실행 (Slack 전송 여부 선택)
make daily-auto   # 자동 모드 (Slack 제외, CI/스케줄러용)
```

### 직접 실행

```bash
# 오늘자 리포트 생성 (Slack 제외)
python3 -m backend.entrypoints.daily_report --skip-slack --auto

# 특정 날짜 리포트 생성
python3 -m backend.entrypoints.daily_report --date 2026-03-26 --skip-slack --auto
```

| 옵션 | 설명 |
|------|------|
| `--date YYYY-MM-DD` | 특정 날짜 기준 리포트 (기본: 오늘 KST) |
| `--skip-review` | GPT 검수 생략 |
| `--skip-service-items` | 서비스 항목 수집 생략 |
| `--skip-slack` | Slack 전송 생략 |
| `--auto` | 자동 모드 (중간 컨펌 없이 진행) |

### 실행 흐름

```
1. 나라장터 스크래핑     (CollectorAgent)
2. GPT 적합/부적합 검수  (ReviewerAgent)
3. 서비스 항목 수집      (ReporterAgent)
4. Firestore 업서트      (ReporterAgent)
5. Slack 전송            (NotifierAgent) ← --skip-slack 없을 때만
```

> Firestore 업서트는 **Upsert(삽입/갱신)만** 수행합니다. 데이터 삭제는 어떤 경우에도 수행하지 않습니다.

---

## CI/CD (GitHub Actions)

매일 **KST 17:00** (UTC 08:00)에 자동 실행됩니다.

### VPN Gate 한국 IP 우회

GitHub Actions는 미국 Azure 서버에서 실행되어 나라장터(g2b.go.kr)가 해외 IP를 차단합니다.
이를 해결하기 위해 **VPN Gate** (일본 쓰쿠바대학 운영, 무료)의 한국 서버를 통해 우회합니다.

```
GitHub Actions Runner (미국)
        │ OpenVPN
        ▼
VPN Gate 한국 서버
        │
        ▼
나라장터 (g2b.go.kr)
```

Playwright 브라우저 트래픽은 별도의 **SOCKS5 프록시(pproxy)**를 통해 VPN 경유를 보장합니다.

### 수동 실행

GitHub Actions 탭 → `Daily Report (자동)` → **Run workflow** 버튼으로 즉시 실행할 수 있습니다.
수동 실행 시 Slack 채널(공식/테스트) 및 VPN 스킵 여부를 선택할 수 있습니다.

### GitHub Secrets 설정 필요

| Secret | 설명 |
|--------|------|
| `FIREBASE_CREDENTIALS` | Firebase 서비스 계정 키 JSON (전체 내용) |
| `OPENAI_API_KEY` | OpenAI API 키 |
| `SLACK_BOT_TOKEN` | Slack Bot Token |

---

## 프론트엔드 주요 기능

### 대시보드 (Home)
- 총 공고 / 적합 / 부적합 / 미검수 통계 카드
- 통계 카드 클릭 시 해당 상태의 최근 공고 목록 필터링
- 검수 현황 도넛 차트
- 기관별 공고 Top 5 수평 바차트
- 최근 7일 수집 추이 라인차트 (KST 기준)

### 공고 목록 (AnnouncementList)
- 적합 / 부적합 / 미검수 탭 필터
- 제목·기관·공고번호 검색
- 게시일 / 수집일 / 예산 정렬
- 50건 단위 페이지네이션

### 공고 상세 (AnnouncementDetail)
- 공고 전체 정보 및 검수 결과 확인
- 적합/부적합 수동 변경

### 경쟁사 동향 (CompetitorTrends)
- `competitor_awards` Firestore 컬렉션 데이터 조회

---

## 데이터 모델 (announcements 컬렉션)

| 필드 | 설명 |
|------|------|
| `title` | 공고 제목 |
| `announcement_number` | 공고 번호 (upsert 기준 키) |
| `agency` | 발주 기관 |
| `publish_date` | 게시일 |
| `deadline` | 마감일 |
| `budget_amount` | 예산 금액 |
| `status` | `approved` / `rejected` / `pending` |
| `display_status` | `20` (노출) / `40` (삭제·숨김) |
| `reviewed` | 검수 완료 여부 (boolean) |
| `created_at` | 수집 일시 (ISO 8601) |
| `source` | 출처 (예: `나라장터`) |
| `review_result` | GPT 검수 결과 상세 |
| `service_items` | 서비스 항목 (PDF 파싱 결과) |

> 상세 스키마는 [SCHEMA_DOCUMENTATION.md](./SCHEMA_DOCUMENTATION.md) 참고

---

## 참고 문서

| 문서 | 내용 |
|------|------|
| [CLAUDE.md](./CLAUDE.md) | AI(Claude Code) 개발 규칙, 운영 워크플로우 |
| [FIREBASE_SETUP.md](./FIREBASE_SETUP.md) | Firebase 서비스 계정 키 및 Firestore 초기 설정 |
| [SCHEMA_DOCUMENTATION.md](./SCHEMA_DOCUMENTATION.md) | Firestore 데이터 스키마 상세 명세 |
