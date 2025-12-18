# 신규 개발자 온보딩 가이드

**메모리가 초기화된 상태에서도 동일한 프로세스를 수행할 수 있도록 작성된 가이드입니다.**

이 문서는 프로젝트를 처음 접하는 개발자가 **처음부터 끝까지** 동일한 결과를 얻을 수 있도록 단계별로 안내합니다.

---

## 🎯 목표

이 가이드를 완료하면:
- ✅ 프로젝트를 어느 환경에서든 클론하여 실행 가능
- ✅ 일일 리포트 생성 프로세스를 완전히 이해
- ✅ 문제 발생 시 스스로 해결 가능

---

## 📋 단계별 온보딩

### Step 1: 프로젝트 클론 및 기본 설정 (10분)

#### 1.1 프로젝트 클론

```bash
git clone <repository-url>
cd eap-intern-roni
```

#### 1.2 백엔드 초기 설정

```bash
cd backend

# Python 가상환경 생성
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# Playwright 브라우저 설치
playwright install chromium
```

#### 1.3 프론트엔드 초기 설정

```bash
cd ../frontend
npm install
```

**✅ 체크포인트**: 의존성 설치가 완료되었는지 확인

---

### Step 2: 환경 변수 설정 (15분)

#### 2.1 Firebase 키 파일 준비

1. Firebase 콘솔 접속: https://console.firebase.google.com
2. 프로젝트 선택 또는 생성
3. 프로젝트 설정 > 서비스 계정 탭
4. "새 비공개 키 생성" 클릭하여 JSON 파일 다운로드
5. 다운로드한 파일을 `backend/config/` 디렉토리에 저장

#### 2.2 .env 파일 생성

```bash
cd backend
touch .env
```

#### 2.3 필수 환경 변수 입력

`.env` 파일에 다음 내용 입력:

```env
# Firebase 설정
FIREBASE_CREDENTIALS_PATH=config/다운로드한-파일명.json

# OpenAI API 설정
OPENAI_API_KEY=sk-your-openai-api-key-here

# 프론트엔드 URL 설정
FRONTEND_URL=http://localhost:3000
```

**자세한 설정 방법**: [ENV_SETUP.md](./ENV_SETUP.md) 참고

**✅ 체크포인트**: 환경 변수가 올바르게 설정되었는지 확인

---

### Step 3: 연결 테스트 (5분)

#### 3.1 Firebase 연결 테스트

```bash
cd backend
python3 scripts/test_firebase.py
```

**예상 출력**:
```
✅ Firebase 초기화 성공
✅ Firestore 연결 성공
```

#### 3.2 스크래퍼 테스트

```bash
python3 scripts/test_scraper.py
```

**예상 출력**:
```
✅ 리포트 파일 생성 완료
수집된 공고 개수: X개
```

**✅ 체크포인트**: 두 테스트가 모두 성공했는지 확인

---

### Step 4: 첫 번째 리포트 생성 (20분)

#### 4.1 나라장터 검색 및 수집

```bash
python3 scripts/test_scraper.py
```

**확인 사항**:
- 리포트 파일 생성: `backend/report/report_YYMMDD.json`
- 수집된 공고 개수 확인

#### 4.2 GPT 검수

```bash
python3 scripts/run_review_cycle.py
```

**확인 사항**:
- 검수 완료 메시지
- 적합/부적합 개수

#### 4.3 적합 공고 첨부파일 분석

```bash
python3 scripts/process_approved_announcements.py --date $(date +%Y-%m-%d)
```

**확인 사항**:
- 적합 공고가 있는 경우에만 실행
- 첨부파일 다운로드 성공 여부

#### 4.4 Firestore 업로드

```bash
python3 scripts/sync_firestore_with_report.py
```

**확인 사항**:
- 업로드 성공 메시지
- Firestore 콘솔에서 데이터 확인

**✅ 체크포인트**: 리포트 파일과 Firestore에 데이터가 올바르게 저장되었는지 확인

---

### Step 5: 프론트엔드 실행 및 확인 (5분)

#### 5.1 프론트엔드 서버 실행

```bash
cd ../frontend
npm start
```

#### 5.2 브라우저에서 확인

브라우저에서 `http://localhost:3000` 접속하여:
- 공고 목록이 표시되는지 확인
- 적합/부적합 공고가 올바르게 표시되는지 확인

**✅ 체크포인트**: 프론트엔드에서 데이터가 올바르게 표시되는지 확인

---

## 🎓 학습 자료

### 필수 문서

1. **[QUICK_START.md](./QUICK_START.md)** - 빠른 시작 가이드
2. **[WORKFLOW_GUIDE.md](./WORKFLOW_GUIDE.md)** - 상세 워크플로우 가이드
3. **[DAILY_CHECKLIST.md](./DAILY_CHECKLIST.md)** - 일일 체크리스트

### 참고 문서

- [SETUP.md](./SETUP.md) - 상세 설치 가이드
- [ENV_SETUP.md](./ENV_SETUP.md) - 환경 변수 설정 가이드
- [backend/scripts/README.md](./backend/scripts/README.md) - 스크립트 사용법

---

## 🔍 프로젝트 구조 이해

### 주요 디렉토리

```
eap-intern-roni/
├── backend/
│   ├── scripts/          # 실행 스크립트
│   │   ├── test_scraper.py                    # 1단계: 나라장터 검색
│   │   ├── run_review_cycle.py                # 2단계: GPT 검수
│   │   ├── process_approved_announcements.py  # 3단계: 첨부파일 분석
│   │   ├── sync_firestore_with_report.py      # 4단계: Firestore 업로드
│   │   └── send_slack_report.py              # 5단계: 슬랙 전송
│   ├── services/         # 비즈니스 로직
│   │   ├── scraper_service.py    # 나라장터 스크래핑
│   │   ├── review_service.py      # GPT 검수
│   │   ├── firebase_service.py    # Firestore 연동
│   │   └── slack_service.py       # 슬랙 전송
│   ├── report/           # 리포트 파일 (report_YYMMDD.json)
│   ├── history/          # 히스토리 파일 (중복 체크용)
│   └── downloads/        # 첨부파일 다운로드 디렉토리
└── frontend/             # React 프론트엔드
```

### 데이터 흐름

```
나라장터 검색
    ↓
report_YYMMDD.json 생성
    ↓
GPT 검수 (status, review_result 추가)
    ↓
적합 공고 첨부파일 분석 (service_items 추가)
    ↓
Firestore 업로드
    ↓
슬랙 메시지 전송
```

---

## 🛠️ 문제 해결

### 자주 발생하는 문제

#### 1. Firebase 연결 실패

**증상**: `Firebase 키 파일을 찾을 수 없습니다`

**해결**:
1. `.env` 파일의 `FIREBASE_CREDENTIALS_PATH` 확인
2. 키 파일이 `backend/config/` 디렉토리에 있는지 확인
3. 파일명이 정확한지 확인

#### 2. OpenAI API 오류

**증상**: `OPENAI_API_KEY가 설정되지 않았습니다`

**해결**:
1. `.env` 파일에 `OPENAI_API_KEY` 추가
2. API 키 유효성 확인: https://platform.openai.com/api-keys
3. API 사용량/크레딧 확인

#### 3. 리포트 파일이 생성되지 않음

**증상**: `검수할 데이터가 없습니다`

**해결**:
1. `test_scraper.py` 실행하여 리포트 파일 생성 확인
2. 나라장터 사이트 접속 가능 여부 확인
3. Playwright 브라우저 재설치: `playwright install chromium`

---

## ✅ 온보딩 완료 체크리스트

다음 항목들을 모두 완료했는지 확인하세요:

- [ ] 프로젝트 클론 및 의존성 설치 완료
- [ ] 환경 변수 설정 완료 (Firebase, OpenAI)
- [ ] Firebase 연결 테스트 성공
- [ ] 스크래퍼 테스트 성공
- [ ] 첫 번째 리포트 생성 성공
- [ ] Firestore 업로드 성공
- [ ] 프론트엔드에서 데이터 확인 완료
- [ ] [WORKFLOW_GUIDE.md](./WORKFLOW_GUIDE.md) 읽기 완료
- [ ] [DAILY_CHECKLIST.md](./DAILY_CHECKLIST.md) 이해 완료

---

## 🎉 다음 단계

온보딩을 완료했다면:

1. **일일 리포트 생성**: [DAILY_CHECKLIST.md](./DAILY_CHECKLIST.md) 따라 매일 리포트 생성
2. **코드 이해**: `backend/services/` 디렉토리의 서비스 코드 읽기
3. **기능 개선**: 필요에 따라 코드 수정 및 개선

---

## 💬 도움이 필요하신가요?

문제가 발생하거나 질문이 있으시면:

1. [WORKFLOW_GUIDE.md](./WORKFLOW_GUIDE.md)의 문제 해결 섹션 확인
2. 프로젝트 이슈 트래커 확인
3. 팀원에게 문의

---

**축하합니다! 🎉 이제 프로젝트를 완전히 이해하고 사용할 수 있습니다.**

