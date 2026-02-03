# EAP 공고 리포트 시스템 아키텍처 문서

## 📋 목차
1. [시스템 개요](#시스템-개요)
2. [아키텍처 개요](#아키텍처-개요)
3. [환경 구성](#환경-구성)
4. [파일 구조](#파일-구조)
5. [작동 프로세스](#작동-프로세스)
6. [Playwright 검색 로직 상세](#playwright-검색-로직-상세)
7. [의존성 및 환경변수](#의존성-및-환경변수)
8. [문제 해결 가이드](#문제-해결-가이드)

---

## 시스템 개요

이 시스템은 나라장터(G2B) 웹사이트에서 EAP(근로자 지원 프로그램) 관련 입찰공고를 자동으로 검색, 수집, 분석하여 리포트를 생성하고 Notion과 Slack에 전송하는 자동화 시스템입니다.

### 주요 기능
- **웹 크롤링**: Playwright를 사용한 브라우저 자동화
- **데이터 필터링**: 중복 제거, 키워드 필터링, 업무구분 필터링
- **AI 검수**: ChatGPT API를 통한 적합/부적합 자동 판정
- **Firestore 저장**: Firebase Firestore에 공고 데이터 저장 및 관리
- **Slack 알림**: 리포트 요약을 Slack 채널로 전송

---

## 아키텍처 개요

### Multi-Agent Skill 아키텍처

시스템은 **Multi-Agent Skill 중심 아키텍처**로 설계되어 있습니다.

#### 핵심 개념

1. **Skill (스킬)**: 재사용 가능한 단일 책임 단위
   - 명확한 입력/출력 계약
   - 부수 효과(파일 쓰기, DB, 슬랙) 명시
   - 다른 에이전트나 오케스트레이터에서 공통 호출 가능

2. **Agent (에이전트)**: 특정 역할을 담당하는 에이전트
   - 해당 역할에 필요한 스킬을 소유·호출
   - 필요 시 다른 에이전트에 위임

3. **Orchestrator (오케스트레이터)**: 워크플로우 관리
   - 사용자 의도를 해석하여 에이전트 호출 순서 결정
   - 컨펌 정책 관리 (interactive vs auto)

#### 아키텍처 다이어그램

```
┌─────────────────────────────────────────┐
│         Orchestrator                    │
│  (워크플로우 관리 및 컨펌 정책)          │
└──────────────┬──────────────────────────┘
               │
    ┌──────────┼──────────┐
    │          │          │
    ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│Collector│ │Reviewer│ │Reporter│ │Notifier│
│ Agent  │ │ Agent  │ │ Agent  │ │ Agent  │
└────┬───┘ └────┬───┘ └────┬───┘ └────┬───┘
     │          │          │          │
     ▼          ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│skill_  │ │skill_  │ │skill_  │ │skill_  │
│scrape_ │ │review_ │ │upsert_ │ │send_   │
│g2b     │ │announc │ │firestor│ │slack_  │
│        │ │ements  │ │e       │ │report  │
└────────┘ └────────┘ └────────┘ └────────┘
```

#### 에이전트 역할

| 에이전트 | 역할 | 보유 스킬 |
|---------|------|----------|
| **CollectorAgent** | 공고 수집 | `skill_scrape_g2b` |
| **ReviewerAgent** | 적합/부적합 검수 | `skill_review_announcements` |
| **ReporterAgent** | Firestore 반영·서비스 항목 | `skill_upsert_firestore`, `skill_collect_service_items` |
| **NotifierAgent** | 슬랙 알림 | `skill_send_slack_report` |

#### 단일 진입점

**일일 리포트 생성**:
```bash
python -m backend.entrypoints.daily_report [옵션]
```

**옵션**:
- `--date YYYY-MM-DD`: 특정 날짜 리포트 생성 (기본값: 오늘 KST)
- `--skip-review`: 검수 단계 건너뛰기
- `--skip-service-items`: 서비스 항목 수집 건너뛰기
- `--skip-slack`: 슬랙 전송 건너뛰기
- `--auto`: 자동 모드 (컨펌 없이 실행, 스케줄/CI용)

**예시**:
```bash
# 오늘자 리포트 생성
python -m backend.entrypoints.daily_report

# 특정 날짜 리포트 생성
python -m backend.entrypoints.daily_report --date 2026-02-03

# 자동 모드 (컨펌 없이 실행)
python -m backend.entrypoints.daily_report --auto
```

#### 컨펌 정책

- **interactive (기본값)**: DB 쓰기·슬랙 전송 전에 사용자에게 확인
- **auto**: `--auto` 플래그 또는 `AUTO_CONFIRM=1` 환경변수 설정 시 자동 실행

---

## 환경 구성

### 운영 체제
- **macOS** (Intel 또는 Apple Silicon)
- Python 3.8 이상

### 필수 소프트웨어
1. **Python 3.8+**
   ```bash
   python3 --version  # 확인
   ```

2. **Playwright 브라우저**
   ```bash
   pip install playwright
   playwright install chromium
   ```

3. **Python 패키지**
   ```bash
   pip install python-dotenv
   pip install slack-sdk
   pip install notion-client
   ```

### 환경변수 설정

프로젝트 루트에 `.env` 파일을 생성하고 다음 변수들을 설정해야 합니다:

```env
# Slack 설정
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_CHANNEL_ID=C071ZL69JQZ

# Notion 설정
NOTION_API_KEY=secret_your-notion-api-key

# Playwright 설정 (선택사항)
PLAYWRIGHT_HEADLESS=false  # true: 브라우저 숨김, false: 브라우저 표시
```

#### 환경변수 획득 방법

**Slack Bot Token:**
1. https://api.slack.com/apps 에서 앱 생성
2. OAuth & Permissions에서 `chat:write` 권한 추가
3. Bot User OAuth Token 복사

**Slack Channel ID:**
1. Slack 채널에서 채널 이름 우클릭 → 채널 세부정보
2. 채널 ID 확인 (C로 시작하는 문자열)

**Notion API Key:**
1. https://www.notion.so/my-integrations 에서 Integration 생성
2. Internal Integration Token 복사
3. Notion 데이터베이스에 Integration 공유 (Share → Integration 추가)

---

## 파일 구조

```
backend/
├── skills/                       # 스킬 모듈 (재사용 가능한 단일 책임 단위)
│   ├── __init__.py
│   ├── scrape.py               # skill_scrape_g2b
│   ├── review.py                # skill_review_announcements
│   ├── firestore.py             # skill_upsert_firestore
│   ├── slack.py                 # skill_send_slack_report
│   └── service_items.py         # skill_collect_service_items
├── agents/                       # 에이전트 모듈
│   ├── collector_agent.py      # CollectorAgent
│   ├── reviewer_agent.py       # ReviewerAgent
│   ├── reporter_agent.py       # ReporterAgent
│   ├── notifier_agent.py       # NotifierAgent
│   ├── code_review_agent.py    # CodeReviewAgent (코드 품질)
│   └── code_optimizer_agent.py # CodeOptimizerAgent (코드 품질)
├── orchestration/                # 오케스트레이터 모듈
│   ├── __init__.py
│   ├── orchestrator.py          # 워크플로우 관리
│   └── policies.py             # 컨펌 정책 관리
├── entrypoints/                  # 단일 진입점
│   ├── __init__.py
│   └── daily_report.py         # 일일 리포트 생성 진입점
├── services/                     # 서비스 레이어 (기존 유지)
│   ├── scraper_service.py
│   ├── review_service.py
│   ├── firebase_service.py
│   ├── slack_service.py
│   └── ...
├── scripts/                      # 스크립트 (하위 호환용)
│   ├── test_scraper.py
│   ├── review_and_upsert_firestore.py
│   └── ...
├── report/                       # 리포트 파일 저장 폴더
│   └── report_YYMMDD.json
└── history/                      # 히스토리 파일 저장 폴더
    └── history_YYMMDD.json
```

---

## 작동 프로세스

### 전체 프로세스 흐름

```
1. Playwright 기반 정보 수집
   ↓
2. 리포트 작성
   ↓
3. 히스토리 저장
   ↓
4. Notion 데이터베이스에 업로드
   ↓
5. QA 가이드 및 사용자 컨펌
   ↓
6. 슬랙 메시지 전송 (사용자 승인 후)
```

### 단계별 상세 설명

#### 1️⃣ Playwright 기반 정보 수집

**목적**: 나라장터 웹사이트에서 입찰공고 검색 및 데이터 추출

**프로세스**:
1. 브라우저 실행 (Chromium)
   - 헤드리스 모드: 환경변수 `PLAYWRIGHT_HEADLESS`로 제어
   - User-Agent: Mac Chrome 설정
   - Viewport: 1920x1080

2. 나라장터 접속
   - URL: `https://www.g2b.go.kr/`
   - 대기: `networkidle` 상태까지 (최대 30초)
   - 추가 대기: 3초

3. 팝업 닫기
   - 팝업 감지: `div[role="dialog"][aria-modal="true"]`
   - 닫기 버튼: `.w2window_close`
   - JavaScript fallback 사용

4. 메뉴 네비게이션
   - 입찰 메뉴 클릭: `#mf_wfm_gnb_wfm_gnbMenu_wq_uuid_567`
   - 입찰공고목록 클릭: `#mf_wfm_gnb_wfm_gnbMenu_genDepth1_1_genDepth2_0_genDepth3_0_btn_menuLvl3`
   - 각 클릭 후 대기: 2-3초

5. 키워드별 검색 반복 (15개 키워드)
   - 각 키워드마다 다음 과정 반복:
     a. 검색 키워드 입력
     b. 날짜 범위 설정 (첫 번째 키워드에서만)
     c. 검색 버튼 클릭
     d. 리스트 갯수 조정 (100개)
     e. 검색 결과 추출

#### 2️⃣ 리포트 작성

**입력 데이터**: 
- `all_bids`: 공고번호를 키로 하는 딕셔너리
- `keyword_included_counts`: 키워드별 포함된 공고 개수

**출력 파일**: 
- `test_report/bid_report_YYYYMMDD.md`

**리포트 구조**:
```markdown
# 📊 EAP 공고 리포트 - YYYY-MM-DD
📅 검색일자: YYYY-MM-DD
📆 검색 기간: YYYYMMDD ~ YYYYMMDD
🔍 검색 키워드: N개
   (키워드별 포함 개수)
📋 통합 검색 결과 수: N개
🚫 중복 제외: N개

## 📋 공고 상세
(각 공고별 상세 정보)
```

#### 3️⃣ 히스토리 저장

**목적**: 다음 리포트에서 중복 제외를 위한 공고번호 저장

**파일 형식**: `history/shared_YYYYMMDD.json`
```json
{
  "date": "YYYYMMDD",
  "bid_nos": ["R25BK01184836", ...],
  "count": 25
}
```

**중요 사항**:
- 오늘 날짜의 히스토리는 **중복 체크에 사용되지 않음**
- 예: 11월 28일 리포트 생성 시 → 11월 27일까지의 히스토지만 참조
- 하루에 여러 번 리포트 생성 시 누락 방지

#### 4️⃣ Notion 데이터베이스에 업로드

**데이터베이스 ID**: `2ab72b4bcb57806da844f33b9c9ce95b`

**프로세스**:
1. 리포트 파일 읽기 (Markdown)
2. Markdown → Notion Blocks 변환
3. 데이터베이스에 새 페이지 생성
4. 페이지 제목 설정: "EAP 공고 리포트 - YYYY-MM-DD"
5. 콘텐츠 블록 추가 (100개씩 배치)

**제목 설정 로직**:
- 리포트 파일명에서 날짜 추출 (`bid_report_YYYYMMDD.md`)
- "이름" 속성 또는 title 타입 속성 찾기
- 생성 후 제목이 비어있으면 업데이트

#### 5️⃣ QA 가이드 및 사용자 컨펌

**체크리스트**:
1. 리포트 파일 내용 확인
2. Notion 문서 확인
3. 히스토리 파일 확인
4. 통계 확인

**사용자 입력**:
- Enter: 슬랙 전송 진행
- `skip` 또는 `s`: 슬랙 전송 건너뛰기

#### 6️⃣ 슬랙 메시지 전송

**메시지 구성**:
1. `:bar_chart: EAP 공고 리포트 - YYYY-MM-DD`
2. `:date: 검색일자`
3. `:calendar: 검색 기간`
4. `:mag: 검색 키워드` (키워드 목록)
5. `:clipboard: 신규 공고` (개수)
6. `전체 리포트 - Notion에서 보기` (링크)

**데이터 추출**:
- 리포트 파일에서 "📋 통합 검색 결과 수: N개" 라인 파싱
- 정규식으로 숫자 추출: `re.search(r'(\d+)', count_part)`

---

## Playwright 검색 로직 상세

### 브라우저 실행 환경

#### 사용 브라우저: Chromium

이 시스템은 **Playwright의 Chromium 브라우저**를 사용합니다. Chromium은 Chrome의 오픈소스 버전으로, 웹 자동화에 최적화되어 있습니다.

**브라우저 설치 위치**:
- macOS: `~/Library/Caches/ms-playwright/chromium-*/`
- Playwright가 자동으로 관리하는 위치에 설치됨

**설치 명령어**:
```bash
playwright install chromium
```

#### 브라우저 실행 방식

**코드**:
```python
with sync_playwright() as p:
    # 브라우저 실행 (헤드리스 모드 설정)
    browser = p.chromium.launch(headless=headless)
    
    context = browser.new_context(
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        viewport={'width': 1920, 'height': 1080}
    )
    
    page = context.new_page()
```

**헤드리스 모드 제어**:
- `headless=True`: 브라우저 창을 표시하지 않음 (백그라운드 실행)
- `headless=False`: 브라우저 창을 화면에 표시 (디버깅 및 확인용)

**헤드리스 모드 결정 순서**:
1. 함수 인자로 `headless` 값이 전달되면 그 값 사용
2. 환경변수 `PLAYWRIGHT_HEADLESS` 확인
   - `'true'`, `'1'`, `'yes'` → 헤드리스 모드 (`headless=True`)
   - 그 외 → 브라우저 표시 (`headless=False`)
3. 기본값: `False` (브라우저 표시)

**환경변수 설정 예시**:
```bash
# .env 파일
PLAYWRIGHT_HEADLESS=false  # 브라우저 표시
PLAYWRIGHT_HEADLESS=true   # 브라우저 숨김
```

#### 브라우저 컨텍스트 설정

**User-Agent 설정**:
```
Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36
```

**의미**:
- macOS 환경을 시뮬레이션
- Chrome 120.0.0.0 버전으로 위장
- 일부 웹사이트에서 봇 차단을 우회하기 위함

**Viewport 설정**:
```python
viewport={'width': 1920, 'height': 1080}
```

**의미**:
- 화면 해상도: 1920x1080 (Full HD)
- 데스크톱 환경을 시뮬레이션
- 반응형 웹사이트에서 데스크톱 레이아웃이 표시되도록 함

#### 브라우저 화면 표시 동작

**헤드리스 모드 OFF (`headless=False`)일 때**:

1. **브라우저 창 자동 열림**
   - 스크립트 실행 시 Chromium 브라우저 창이 자동으로 열림
   - 일반 Chrome 브라우저와 유사한 UI
   - 주소창, 탭, 개발자 도구 등 모든 기능 사용 가능

2. **실시간 동작 확인**
   - 페이지 이동, 클릭, 입력 등 모든 동작을 실시간으로 확인 가능
   - 디버깅 및 문제 해결에 유용

3. **자동 닫힘**
   - 스크립트 종료 시 브라우저가 자동으로 닫힘
   - 예외 발생 시에도 `finally` 블록에서 닫힘

4. **15초 대기 시간**
   - 스크립트 완료 후 브라우저를 15초간 열어둠
   - 사용자가 결과를 확인할 수 있도록 함
   ```python
   if not headless:
       print("\n⏳ 브라우저를 15초간 열어둡니다. 확인해보세요...")
       time.sleep(15)
   ```

**헤드리스 모드 ON (`headless=True`)일 때**:

1. **백그라운드 실행**
   - 브라우저 창이 표시되지 않음
   - 시스템 리소스만 사용
   - 서버 환경이나 자동화 스케줄링에 적합

2. **동일한 기능**
   - 헤드리스 모드여도 모든 기능은 동일하게 작동
   - 페이지 렌더링, JavaScript 실행 등 모두 정상 작동

#### 브라우저 실행 예시

**화면에 브라우저 표시 (기본값)**:
```bash
# .env 파일 없음 또는 PLAYWRIGHT_HEADLESS=false
python3 test/g2b_full_search_and_extract.py
# → Chromium 브라우저 창이 화면에 표시됨
```

**브라우저 숨김 (헤드리스 모드)**:
```bash
# .env 파일에 PLAYWRIGHT_HEADLESS=true 설정
python3 test/g2b_full_search_and_extract.py
# → 브라우저 창이 표시되지 않음 (백그라운드 실행)
```

**프로그래밍 방식으로 제어**:
```python
# 브라우저 표시
search_and_extract_bids(headless=False)

# 브라우저 숨김
search_and_extract_bids(headless=True)
```

#### 브라우저 실행 환경 요약

| 항목 | 값/설정 |
|------|---------|
| 브라우저 엔진 | Chromium (Playwright) |
| 기본 모드 | 헤드리스 OFF (브라우저 표시) |
| User-Agent | Mac Chrome 120.0.0.0 |
| Viewport | 1920x1080 |
| 자동 닫힘 | 스크립트 종료 시 |
| 대기 시간 | 헤드리스 OFF일 때 15초 |
| 설치 위치 | `~/Library/Caches/ms-playwright/chromium-*/` |

#### 브라우저 디버깅 팁

**브라우저를 표시하여 문제 확인**:
1. `.env` 파일에 `PLAYWRIGHT_HEADLESS=false` 설정
2. 스크립트 실행
3. 브라우저 창에서 실제 동작 확인
4. 개발자 도구 (F12)로 요소 확인 가능

**느린 실행 속도 조정**:
- 헤드리스 모드 사용 시 더 빠름
- `time.sleep()` 값 조정 가능 (코드 내)

### 화면 클릭 및 상호작용 요소

#### 1. 페이지 접속 및 초기화

**나라장터 메인 페이지 접속**:
```python
url = "https://www.g2b.go.kr/"
page.goto(url, wait_until="networkidle", timeout=30000)
time.sleep(3)  # 페이지 로딩 대기
```

**중요 사항**:
- `wait_until="networkidle"`: 네트워크 요청이 완료될 때까지 대기
- `timeout=30000`: 최대 30초 대기
- 추가 3초 대기: JavaScript 실행 및 동적 콘텐츠 로딩 대기

#### 2. 팝업 닫기

**팝업 감지**:
```python
popup_selector = 'div[role="dialog"][aria-modal="true"]'
if page.locator(popup_selector).count() > 0:
```

**팝업 닫기 버튼 클릭**:
- **CSS 선택자**: `.w2window_close`
- **방법 1**: Playwright Locator 사용
  ```python
  close_button = page.locator('.w2window_close').first
  close_button.click(timeout=3000)
  ```
- **방법 2**: JavaScript fallback (방법 1 실패 시)
  ```python
  page.evaluate("() => { 
      const btn = document.querySelector('.w2window_close'); 
      if (btn) btn.click(); 
  }")
  ```
- **대기 시간**: 클릭 후 1초 대기

**왜 두 가지 방법을 사용하는가?**
- 일부 팝업은 JavaScript 이벤트가 필요할 수 있음
- Playwright 클릭이 실패할 경우를 대비한 fallback

#### 3. 메뉴 네비게이션

**입찰 메뉴 클릭**:
- **요소 ID**: `mf_wfm_gnb_wfm_gnbMenu_wq_uuid_567`
- **클릭 방법**: JavaScript 직접 실행
  ```python
  page.evaluate(f"""
      () => {{
          const el = document.getElementById('{menu_bid_id}');
          if (el) el.click();
      }}
  """)
  time.sleep(2)  # 메뉴 확장 대기
  ```

**입찰공고목록 메뉴 클릭**:
- **요소 ID**: `mf_wfm_gnb_wfm_gnbMenu_genDepth1_1_genDepth2_0_genDepth3_0_btn_menuLvl3`
- **클릭 방법**: JavaScript 직접 실행
  ```python
  page.evaluate(f"""
      () => {{
          const el = document.getElementById('{menu_bid_list_id}');
          if (el) el.click();
      }}
  """)
  time.sleep(3)  # 페이지 로딩 대기
  ```

**중요 사항**:
- JavaScript를 사용하는 이유: 일부 메뉴는 Playwright의 일반 클릭으로 작동하지 않을 수 있음
- 대기 시간: 메뉴 확장 및 페이지 로딩을 위해 충분한 시간 필요

### 검색 진행 로직 (단계별 상세)

#### 단계 1: 검색 키워드 입력

**요소 ID**: `mf_wfm_container_tacBidPbancLst_contents_tab2_body_bidPbancNm`

**입력 방법 1: Playwright Locator (주요 방법)**:
```python
keyword_input = page.locator(f'#{keyword_input_id}')
if keyword_input.count() > 0:
    keyword_input.clear()  # 기존 값 삭제
    keyword_input.fill(keyword)  # 새 키워드 입력
    time.sleep(0.5)  # 입력 완료 대기
```

**입력 방법 2: JavaScript fallback (방법 1 실패 시)**:
```python
page.evaluate(f"""
    () => {{
        const el = document.getElementById('{keyword_input_id}');
        if (el) {{
            el.value = '{keyword}';
            el.dispatchEvent(new Event('input', {{ bubbles: true }}));
            el.dispatchEvent(new Event('change', {{ bubbles: true }}));
        }}
    }}
""")
```

**중요 사항**:
- `clear()`: 기존 검색어 삭제 (이전 검색 결과 영향 방지)
- `fill()`: 새 키워드 입력
- JavaScript fallback: `input` 및 `change` 이벤트를 수동으로 발생시켜 웹사이트가 변경을 감지하도록 함
- **에러 처리**: 요소를 찾을 수 없으면 해당 키워드 건너뛰기 (`continue`)

#### 단계 2: 날짜 범위 설정

**요소 ID**: `wq_uuid_2223_grpCalRoot`

**실행 조건**: 첫 번째 키워드에서만 실행 (한 번만 설정하면 이후 검색에 유지됨)

**날짜 형식**: `YYYYMMDD` (예: `20251128`)

**설정 프로세스**:
1. 날짜 범위 컨테이너 찾기
   ```python
   date_range_element = page.locator(f'#{date_range_id}')
   ```

2. 내부 input 요소 탐색 (JavaScript)
   ```python
   date_inputs = page.evaluate(f"""
       () => {{
           const container = document.getElementById('{date_range_id}');
           if (container) {{
               const inputs = container.querySelectorAll('input[type="text"], input[type="date"]');
               return Array.from(inputs).map(inp => ({{
                   id: inp.id || '',
                   name: inp.name || '',
                   value: inp.value || ''
               }}));
           }}
           return [];
       }}
   """)
   ```

3. 시작일 입력 (첫 번째 input)
   ```python
   if len(date_inputs) >= 1:
       start_input = page.locator(f'#{date_inputs[0]["id"]}')
       start_input.fill(start_date_str)  # 예: "20251114"
   ```

4. 종료일 입력 (두 번째 input)
   ```python
   if len(date_inputs) >= 2:
       end_input = page.locator(f'#{date_inputs[1]["id"]}')
       end_input.fill(end_date_str)  # 예: "20251128"
   ```

**중요 사항**:
- 날짜 범위 요소를 찾을 수 없어도 계속 진행 (선택사항)
- 각 입력 후 0.5초 대기
- 날짜 형식은 반드시 `YYYYMMDD` (하이픈 없음)

#### 단계 3: 검색 버튼 클릭

**요소 ID**: `mf_wfm_container_tacBidPbancLst_contents_tab2_body_btnS0004`

**클릭 방법 1: Playwright Locator (주요 방법)**:
```python
search_button = page.locator(f'#{search_button_id}')
if search_button.count() > 0:
    search_button.click(timeout=5000)
    time.sleep(5)  # 검색 결과 로딩 대기
```

**클릭 방법 2: JavaScript fallback**:
```python
page.evaluate(f"""
    () => {{
        const el = document.getElementById('{search_button_id}');
        if (el && !el.disabled) el.click();
    }}
""")
time.sleep(5)
```

**중요 사항**:
- `timeout=5000`: 버튼이 클릭 가능할 때까지 최대 5초 대기
- 클릭 후 5초 대기: 검색 결과가 로드될 때까지 충분한 시간
- JavaScript fallback: 버튼이 비활성화되어 있지 않은지 확인 (`!el.disabled`)
- **에러 처리**: 검색 버튼을 찾을 수 없으면 해당 키워드 건너뛰기 (`continue`)

#### 단계 4: 리스트 갯수 조정

**요소 ID**: `mf_wfm_container_tacBidPbancLst_contents_tab2_body_sbxRecordCountPerPage1`

**목표**: 한 페이지에 표시되는 공고 수를 100개로 설정

**설정 방법 1: Playwright Select (주요 방법)**:
```python
record_count_select = page.locator(f'#{record_count_select_id}')
record_count_select.select_option("100")
time.sleep(1)
```

**설정 방법 2: JavaScript fallback**:
```python
page.evaluate(f"""
    () => {{
        const el = document.getElementById('{record_count_select_id}');
        if (el) {{
            if (el.tagName === 'SELECT') {{
                el.value = '100';
                el.dispatchEvent(new Event('change', {{ bubbles: true }}));
            }}
        }}
    }}
""")
```

**적용 버튼 클릭**:
- **요소 ID**: `mf_wfm_container_tacBidPbancLst_contents_tab2_body_btnAplcn1`
- **클릭 방법**: Playwright Locator 또는 JavaScript fallback
- **대기 시간**: 클릭 후 3초 대기 (리스트 갱신 대기)

**중요 사항**:
- 리스트 갯수 변경 후 반드시 적용 버튼 클릭 필요
- `change` 이벤트 발생: 웹사이트가 변경을 감지하도록 함
- 각 키워드마다 수행: 검색 결과가 초기화될 수 있으므로

### 데이터 수집 로직 (상세)

#### 데이터 추출 방식

**JavaScript 실행 컨텍스트 사용**:
- `page.evaluate()`: 브라우저의 JavaScript 실행 환경에서 코드 실행
- DOM에 직접 접근하여 데이터 추출
- 브라우저에서 렌더링된 실제 HTML을 기반으로 작동

#### 추출 방법 1: 링크 기반 추출 (주요 방법)

**공고번호 패턴**:
```javascript
const bidNoPattern = /R\d{2}[A-Z]{2}\d{8}/;
// 예: R25BK01184836
```

**링크 선택자**:
```javascript
const links = Array.from(document.querySelectorAll(
    'a[href*="bidno"], a[href*="bidPbancNo"], a[href*="coDetail"]'
));
```

**추출 프로세스**:
1. 공고번호 패턴이 있는 링크 찾기
2. 각 링크의 부모 행(`<tr>`) 찾기
3. 행의 모든 셀(`<td>`) 추출
4. 업무구분 필터링: "일반용역"만 포함
5. 공고번호, 공고명, 공고일, 기관 정보 추출

**업무구분 필터링 로직**:
```javascript
// 업무구분 컬럼 인덱스 찾기
let businessTypeColumnIndex = -1;
const gridView = document.querySelector('[id*="gridView1"]');
// 헤더에서 "업무구분" 또는 column27 찾기
// ...

// 업무구분이 "일반용역"인지 확인
if (businessTypeColumnIndex >= 0 && businessTypeColumnIndex < cells.length) {
    const businessTypeCell = cells[businessTypeColumnIndex];
    const businessType = businessTypeCell ? businessTypeCell.innerText.trim() : '';
    if (businessType !== '일반용역') {
        return; // 일반용역이 아니면 제외
    }
}
```

**달력 데이터 제외**:
```javascript
// 달력 데이터가 아닌 실제 공고 데이터인지 확인
const rowText = row.innerText.trim();
if (rowText.length > 20 && !rowText.match(/\d{1,2}\s+\d{1,2}\s+\d{1,2}/)) {
    // 실제 공고 데이터 처리
}
```

#### 추출 방법 2: 테이블 기반 추출 (보조 방법)

**사용 조건**: 방법 1에서 공고를 찾지 못한 경우 (`bids.length === 0`)

**프로세스**:
1. 모든 `<table>` 요소 찾기
2. 각 테이블에서 헤더 행 찾기
   - 헤더 키워드: "공고번호", "공고명", "공고일", "기관", "입찰", "마감"
   - 달력 패턴 제외: `/\d{1,2}\s+\d{1,2}\s+\d{1,2}/`
3. 헤더 행 이후의 데이터 행 순회
4. 업무구분 필터링: "일반용역"만 포함
5. 공고번호 패턴 매칭하여 공고 추출

**데이터 구조**:
```javascript
const bidData = {
    '공고번호': 'R25BK01184836',
    '공고명': '2026년 소방공무원 찾아가는 상담실 업무위탁',
    '공고일': '2025-11-27',
    '기관': '세종특별자치시 소방본부',
    'link': 'https://...'
};
```

#### 데이터 필터링 (Python 측)

**중복 제거**:
```python
if bid_no in shared_bid_nos:
    skipped_count += 1
    continue  # 제외
```

**타이틀 필터링**:
```python
# 제외 키워드 체크
exclude_keywords = [
    "비상대처계획", "시험", "정비공사", "시스템", 
    "공사", "납품", "청소", "홍보", "복지관"
]

# "복지관" 특별 처리
if "복지관" in bid_title:
    should_exclude = True
else:
    # 다른 제외 키워드 체크
    for exclude_kw in exclude_keywords:
        if exclude_kw == "복지관":
            continue
        if exclude_kw in bid_title:
            should_exclude = True
            break
```

**키워드 매칭 정보 추가**:
```python
if bid_no not in all_bids:
    bid['매칭키워드'] = [keyword]
    all_bids[bid_no] = bid
else:
    # 이미 존재하는 공고인 경우 키워드만 추가
    if keyword not in all_bids[bid_no].get('매칭키워드', []):
        all_bids[bid_no]['매칭키워드'].append(keyword)
```

### 검색이 안 될 때 확인 사항

#### 1. 요소를 찾을 수 없는 경우

**증상**:
- "❌ 검색 입력 필드를 찾을 수 없습니다!"
- "❌ 검색 버튼을 찾을 수 없습니다!"

**원인**:
- 나라장터 웹사이트 구조 변경
- 페이지 로딩이 완료되지 않음
- JavaScript가 아직 실행되지 않음

**해결 방법**:
1. 브라우저를 표시 모드로 실행 (`PLAYWRIGHT_HEADLESS=false`)
2. 개발자 도구(F12)로 실제 요소 ID 확인
3. 대기 시간 증가 (`time.sleep()` 값 조정)
4. `wait_until` 옵션 변경 (`"load"`, `"domcontentloaded"` 등)

#### 2. 검색 버튼 클릭이 작동하지 않는 경우

**증상**:
- 검색 버튼을 클릭해도 아무 일도 일어나지 않음
- 검색 결과가 나타나지 않음

**원인**:
- 버튼이 비활성화되어 있음
- JavaScript 이벤트가 필요함
- 페이지가 완전히 로드되지 않음

**해결 방법**:
1. JavaScript fallback 사용 (코드에 이미 포함됨)
2. 버튼이 활성화될 때까지 대기
   ```python
   page.wait_for_selector(f'#{search_button_id}:not([disabled])')
   ```
3. 네트워크 요청 완료 대기
   ```python
   page.wait_for_load_state("networkidle")
   ```

#### 3. 검색 결과가 0개인 경우

**증상**:
- "✅ 공고 데이터 추출 완료: 0개"

**원인**:
- 검색 조건에 맞는 공고가 실제로 없음
- 데이터 추출 로직이 페이지 구조를 제대로 파악하지 못함
- 업무구분 필터링이 너무 엄격함

**해결 방법**:
1. 브라우저에서 수동으로 검색하여 결과 확인
2. 개발자 도구로 실제 HTML 구조 확인
3. JavaScript 추출 코드의 선택자 수정
4. 업무구분 필터링 임시 제거하여 테스트

#### 4. 날짜 범위 설정이 작동하지 않는 경우

**증상**:
- 날짜 입력 필드를 찾을 수 없음
- 날짜가 입력되지 않음

**원인**:
- 날짜 입력 필드의 ID가 변경됨
- 날짜 형식이 맞지 않음
- JavaScript로 동적으로 생성되는 요소

**해결 방법**:
1. 날짜 범위 설정은 선택사항이므로 건너뛰어도 검색 가능
2. 개발자 도구로 실제 날짜 입력 필드 확인
3. 다른 선택자 시도 (`input[type="date"]`, `input[name*="date"]` 등)

### 디버깅 팁

#### 브라우저 표시 모드로 실행

```bash
# .env 파일
PLAYWRIGHT_HEADLESS=false
```

#### 각 단계별 스크린샷 저장

코드에 추가:
```python
page.screenshot(path=f"debug_step_{keyword_idx}.png")
```

#### 개발자 도구로 요소 확인

브라우저가 표시되는 모드에서:
1. F12로 개발자 도구 열기
2. Elements 탭에서 실제 요소 ID 확인
3. Console 탭에서 JavaScript 실행 테스트

#### 로그 확인

코드는 각 단계마다 상세한 로그를 출력합니다:
- `✅`: 성공
- `⚠️`: 경고 (계속 진행)
- `❌`: 오류 (건너뛰기)

### 요소 선택자 요약

| 요소 | ID | 용도 |
|------|-----|------|
| 검색 입력 필드 | `mf_wfm_container_tacBidPbancLst_contents_tab2_body_bidPbancNm` | 키워드 입력 |
| 날짜 범위 컨테이너 | `wq_uuid_2223_grpCalRoot` | 날짜 범위 설정 |
| 검색 버튼 | `mf_wfm_container_tacBidPbancLst_contents_tab2_body_btnS0004` | 검색 실행 |
| 리스트 갯수 선택 | `mf_wfm_container_tacBidPbancLst_contents_tab2_body_sbxRecordCountPerPage1` | 페이지당 항목 수 설정 |
| 적용 버튼 | `mf_wfm_container_tacBidPbancLst_contents_tab2_body_btnAplcn1` | 리스트 갯수 변경 적용 |
| 입찰 메뉴 | `mf_wfm_gnb_wfm_gnbMenu_wq_uuid_567` | 메뉴 네비게이션 |
| 입찰공고목록 메뉴 | `mf_wfm_gnb_wfm_gnbMenu_genDepth1_1_genDepth2_0_genDepth3_0_btn_menuLvl3` | 메뉴 네비게이션 |
| 팝업 닫기 버튼 | `.w2window_close` (CSS 선택자) | 팝업 닫기 |

### 검색 키워드 입력 로직

**방법 1: Playwright Locator 사용**
```python
keyword_input = page.locator(f'#{keyword_input_id}')
keyword_input.clear()
keyword_input.fill(keyword)
```

**방법 2: JavaScript fallback**
```python
page.evaluate(f"""
    () => {{
        const el = document.getElementById('{keyword_input_id}');
        if (el) {{
            el.value = '{keyword}';
            el.dispatchEvent(new Event('input', {{ bubbles: true }}));
            el.dispatchEvent(new Event('change', {{ bubbles: true }}));
        }}
    }}
""")
```

### 날짜 범위 설정 로직

**첫 번째 키워드에서만 실행**:
1. 날짜 범위 컨테이너 찾기
2. 내부 input 요소들 탐색
3. 첫 번째 input: 시작일 (`YYYYMMDD` 형식)
4. 두 번째 input: 종료일 (`YYYYMMDD` 형식)

**날짜 형식**: `YYYYMMDD` (예: `20251128`)

### 검색 결과 추출 로직

**JavaScript 실행 컨텍스트**:
- 페이지의 DOM을 직접 조작하여 데이터 추출
- `page.evaluate()` 사용

**추출 방법 1: 링크 기반 추출**
```javascript
const links = Array.from(document.querySelectorAll('a[href*="bidno"], a[href*="bidPbancNo"], a[href*="coDetail"]'));
// 공고번호 패턴: R\d{2}[A-Z]{2}\d{8}
```

**추출 방법 2: 테이블 기반 추출**
- 테이블 헤더 찾기
- 데이터 행 순회
- 공고번호 패턴 매칭

**업무구분 필터링**:
- 컬럼 인덱스 찾기: "업무구분" 또는 `column27`
- "일반용역"만 포함

**데이터 구조**:
```python
{
    '공고번호': 'R25BK01184836',
    '공고명': '2026년 소방공무원 찾아가는 상담실 업무위탁',
    '공고일': '2025-11-27',
    '기관': '세종특별자치시 소방본부',
    'link': 'https://...',
    '매칭키워드': ['찾아가는 상담실', '상담']
}
```

### 중복 제거 로직

**히스토리 로드**:
```python
# 오늘 이전의 모든 히스토리 파일 로드
history_check_start_date = datetime(2025, 1, 1)
current_check_date = history_check_start_date
today_date_only = today_date.date()

while current_check_date.date() < today_date_only:
    # history/shared_YYYYMMDD.json 파일 읽기
    # bid_nos 집합에 추가
```

**중복 체크**:
```python
if bid_no in shared_bid_nos:
    skipped_count += 1
    continue  # 제외
```

### 키워드 필터링 로직

**제외 키워드 목록**:
```python
exclude_keywords = [
    "비상대처계획",
    "시험",
    "정비공사",
    "시스템",
    "공사",
    "납품",
    "청소",
    "홍보",
    "복지관"  # 특별 처리
]
```

**"복지관" 특별 처리**:
```python
if "복지관" in bid_title:
    should_exclude = True  # 제외
else:
    # "복지"만 있으면 포함 (제외하지 않음)
    for exclude_kw in exclude_keywords:
        if exclude_kw == "복지관":
            continue  # 이미 처리했으므로 스킵
        if exclude_kw in bid_title:
            should_exclude = True
            break
```

**업무구분 필터링**:
- JavaScript에서 "일반용역"만 추출
- Python에서도 재확인

---

## 의존성 및 환경변수

### Python 패키지

**필수 패키지**:
```bash
pip install playwright
pip install python-dotenv
pip install slack-sdk
pip install notion-client
```

**Playwright 브라우저 설치**:
```bash
playwright install chromium
```

### 환경변수 (.env 파일)

**필수 변수**:
```env
SLACK_BOT_TOKEN=xoxb-...
SLACK_CHANNEL_ID=C071ZL69JQZ
NOTION_API_KEY=secret_...
```

**선택 변수**:
```env
PLAYWRIGHT_HEADLESS=false  # 기본값: false
```

### 시스템 요구사항

**macOS**:
- Python 3.8 이상
- 충분한 디스크 공간 (Playwright 브라우저 ~200MB)
- 인터넷 연결

**권장 사양**:
- RAM: 4GB 이상
- CPU: 최신 Intel 또는 Apple Silicon

---

## 문제 해결 가이드

### 일반적인 문제

#### 1. Playwright 브라우저를 찾을 수 없음

**증상**:
```
Error: Executable doesn't exist
```

**해결**:
```bash
playwright install chromium
```

#### 2. 환경변수를 찾을 수 없음

**증상**:
```
❌ SLACK_BOT_TOKEN 환경변수가 설정되지 않았습니다.
```

**해결**:
1. 프로젝트 루트에 `.env` 파일 생성 확인
2. `.env` 파일 내용 확인
3. `python-dotenv` 설치 확인: `pip install python-dotenv`

#### 3. Notion 페이지 제목이 비어있음

**증상**:
- Notion 페이지가 생성되지만 제목이 비어있음

**원인**:
- 데이터베이스의 title 속성 이름이 예상과 다름
- Notion API 권한 문제

**해결**:
1. Notion 데이터베이스에서 "이름" 속성 확인
2. Integration이 데이터베이스에 공유되어 있는지 확인
3. `upload_to_notion.py`의 디버그 출력 확인

#### 4. 검색 결과가 0개

**증상**:
- 모든 키워드에서 검색 결과가 0개

**원인**:
- 나라장터 웹사이트 구조 변경
- 네트워크 문제
- 요소 선택자 변경

**해결**:
1. 브라우저가 표시되는 모드로 실행 (`PLAYWRIGHT_HEADLESS=false`)
2. 수동으로 나라장터 접속하여 검색 테스트
3. 브라우저 개발자 도구로 요소 ID 확인
4. `g2b_full_search_and_extract.py`의 선택자 업데이트

#### 5. 슬랙 메시지 전송 실패

**증상**:
```
❌ 슬랙 API 오류: invalid_auth
```

**해결**:
1. `SLACK_BOT_TOKEN` 확인
2. Slack 앱의 권한 확인 (`chat:write`)
3. 채널에 봇이 초대되어 있는지 확인

### 디버깅 팁

#### 브라우저 표시 모드로 실행

`.env` 파일에 추가:
```env
PLAYWRIGHT_HEADLESS=false
```

또는 스크립트 실행 시:
```python
search_and_extract_bids(headless=False)
```

#### 로그 확인

스크립트는 각 단계마다 상세한 로그를 출력합니다:
- `✅`: 성공
- `⚠️`: 경고 (계속 진행)
- `❌`: 오류 (중단)

#### 수동 테스트

개별 모듈 테스트:
```bash
# Slack 전송만 테스트
python3 test/send_to_slack.py test_report/bid_report_20251128.md

# Notion 업로드만 테스트
python3 test/upload_to_notion.py test_report/bid_report_20251128.md
```

### 환경 차이점 체크리스트

다른 맥북에서 구축 시 확인 사항:

- [ ] Python 버전 동일 (`python3 --version`)
- [ ] 모든 패키지 설치 확인 (`pip list`)
- [ ] Playwright 브라우저 설치 확인 (`playwright install chromium`)
- [ ] `.env` 파일 존재 및 내용 확인
- [ ] 인터넷 연결 확인
- [ ] 나라장터 웹사이트 접속 가능 여부 확인
- [ ] Notion API 토큰 유효성 확인
- [ ] Slack Bot Token 유효성 확인
- [ ] 파일 권한 확인 (쓰기 권한)

---

## 실행 방법

### 기본 실행

```bash
cd /path/to/naramarket-mcp-slack
python3 test/g2b_full_search_and_extract.py
```

### 테스트 모드 (단일 키워드)

```bash
python3 test/g2b_full_search_and_extract.py "EAP"
```

### 스케줄링 (cron)

`scripts/run_daily_report.sh` 참고

---

## 추가 참고사항

### 키워드 목록

현재 검색 키워드 (15개):
1. EAP
2. 근로자 지원 프로그램
3. 근로자지원프로그램
4. 찾아가는 상담실
5. 심리
6. 치유
7. 상담
8. 복지
9. 치료
10. 근로자
11. 감정
12. 정서
13. 행복
14. 마음
15. 힐링

### 검색 기간

- 기본: 오늘 기준 14일 전 ~ 오늘
- 날짜 형식: `YYYYMMDD`

### 리포트 파일명 규칙

- 형식: `bid_report_YYYYMMDD.md`
- 예: `bid_report_20251128.md`

### 히스토리 파일명 규칙

- 형식: `shared_YYYYMMDD.json`
- 예: `shared_20251128.json`

---

## 문의 및 지원

문제가 발생하면 다음을 확인하세요:
1. 이 문서의 "문제 해결 가이드" 섹션
2. 스크립트의 로그 출력
3. 브라우저 표시 모드로 실행하여 시각적 확인

---

**문서 버전**: 1.0  
**최종 업데이트**: 2025-11-28

