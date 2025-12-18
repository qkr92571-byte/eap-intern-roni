# 빠른 시작 가이드

**메모리가 초기화된 상태에서도 동일한 프로세스를 수행할 수 있도록 작성된 가이드입니다.**

---

## 📦 사전 요구사항

- Python 3.8 이상
- Node.js 16 이상 및 npm
- Git

---

## 🚀 1단계: 프로젝트 클론 및 초기 설정

### 1.1 프로젝트 클론

```bash
git clone <repository-url>
cd eap-intern-roni
```

### 1.2 백엔드 설정

```bash
# 백엔드 디렉토리로 이동
cd backend

# Python 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# Playwright 브라우저 설치
playwright install chromium
```

### 1.3 환경 변수 설정

```bash
# .env 파일 생성 (예시 파일 복사)
cp .env.example .env

# .env 파일 편집하여 실제 값 입력
# 필수 항목:
# - FIREBASE_CREDENTIALS_PATH
# - OPENAI_API_KEY
# - FRONTEND_URL
```

**필수 환경 변수**:
- `FIREBASE_CREDENTIALS_PATH`: Firebase 키 파일 경로
- `OPENAI_API_KEY`: OpenAI API 키
- `FRONTEND_URL`: 프론트엔드 서버 주소 (예: `http://172.30.1.17:3000`)

**선택 환경 변수** (슬랙 알림 사용 시):
- `SLACK_BOT_TOKEN`: Slack Bot Token
- `SLACK_CHANNEL_ID`: Slack 채널 ID
- `SLACK_EAP_USERGROUP`: Slack 유저그룹 ID

### 1.4 Firebase 키 파일 설정

1. Firebase 콘솔 접속: https://console.firebase.google.com
2. 프로젝트 선택 또는 생성
3. 프로젝트 설정 > 서비스 계정 탭
4. "새 비공개 키 생성" 클릭하여 JSON 파일 다운로드
5. 다운로드한 파일을 `backend/config/` 디렉토리에 저장
6. `.env` 파일의 `FIREBASE_CREDENTIALS_PATH`에 파일명 지정

### 1.5 프론트엔드 설정

```bash
# 프론트엔드 디렉토리로 이동
cd ../frontend

# 의존성 설치
npm install
```

---

## ✅ 2단계: 초기 설정 확인

### 2.1 Firebase 연결 테스트

```bash
cd backend
python3 scripts/test_firebase.py
```

**예상 출력**:
```
✅ Firebase 초기화 성공
✅ Firestore 연결 성공
```

### 2.2 스크래퍼 테스트

```bash
python3 scripts/test_scraper.py
```

**예상 출력**:
```
✅ 리포트 파일 생성 완료
수집된 공고 개수: X개
```

---

## 📅 3단계: 일일 리포트 생성 (전체 프로세스)

### 방법 1: 단계별 실행 (권장 - 처음 사용 시)

```bash
cd backend

# 1. 나라장터 검색 및 수집
python3 scripts/test_scraper.py

# 2. GPT 검수
python3 scripts/run_review_cycle.py

# 3. 적합 공고 첨부파일 분석 (적합 공고가 있는 경우만)
python3 scripts/process_approved_announcements.py --date $(date +%Y-%m-%d)

# 4. Firestore 업로드
python3 scripts/sync_firestore_with_report.py

# 5. 슬랙 메시지 전송 (선택사항)
python3 scripts/send_slack_report.py $(date +%y%m%d)
```

### 방법 2: 통합 스크립트 사용

```bash
cd backend

# 전체 워크플로우 자동 실행 (슬랙 전송 제외)
python3 scripts/review_and_upload_report.py --skip-slack --auto-upload

# 슬랙 전송은 별도로 실행
python3 scripts/send_slack_report.py $(date +%y%m%d)
```

---

## 🔍 4단계: 결과 확인

### 리포트 파일 확인

```bash
# 오늘 날짜 리포트 확인
cat backend/report/report_$(date +%y%m%d).json | jq '. | length'
```

### Firestore 확인

1. Firebase 콘솔 접속: https://console.firebase.google.com
2. Firestore Database 탭
3. `announcements` 컬렉션 확인

### 프론트엔드 확인

```bash
cd frontend
npm start
```

브라우저에서 `http://localhost:3000` 접속하여 공고 목록 확인

---

## 🛠️ 문제 해결

### Python 가상환경 활성화 실패

**macOS/Linux**:
```bash
source venv/bin/activate
```

**Windows**:
```bash
venv\Scripts\activate
```

### Playwright 브라우저 설치 실패

```bash
playwright install chromium
# 또는
playwright install --with-deps chromium
```

### Firebase 연결 실패

1. `.env` 파일의 `FIREBASE_CREDENTIALS_PATH` 확인
2. 키 파일이 올바른 경로에 있는지 확인
3. Firebase 콘솔에서 프로젝트 ID 확인

### OpenAI API 오류

1. `.env` 파일에 `OPENAI_API_KEY` 설정 확인
2. API 키 유효성 확인: https://platform.openai.com/api-keys
3. API 사용량/크레딧 확인

---

## 📚 추가 문서

- [WORKFLOW_GUIDE.md](./WORKFLOW_GUIDE.md) - 상세 워크플로우 가이드
- [SETUP.md](./SETUP.md) - 상세 설치 가이드
- [backend/scripts/README.md](./backend/scripts/README.md) - 스크립트 사용법

---

## 💡 자주 묻는 질문 (FAQ)

### Q: 매일 수동으로 실행해야 하나요?

A: 네, 현재는 수동 실행입니다. 자동화를 원하시면 Cron이나 스케줄러를 설정하세요.

### Q: 리포트 파일은 어디에 저장되나요?

A: `backend/report/report_YYMMDD.json` 파일로 저장됩니다.

### Q: Firestore에 업로드하지 않고 리포트만 생성할 수 있나요?

A: 네, 1-2단계만 실행하면 리포트 파일만 생성됩니다.

### Q: 슬랙 메시지를 보내지 않고 리포트만 생성할 수 있나요?

A: 네, 1-4단계만 실행하면 슬랙 전송 없이 리포트 생성 및 Firestore 업로드만 수행됩니다.

---

## 🎯 체크리스트

초기 설정 완료 확인:

- [ ] Python 가상환경 생성 및 활성화
- [ ] 백엔드 의존성 설치 완료
- [ ] Playwright 브라우저 설치 완료
- [ ] `.env` 파일 생성 및 필수 환경 변수 설정
- [ ] Firebase 키 파일 설정 완료
- [ ] 프론트엔드 의존성 설치 완료
- [ ] Firebase 연결 테스트 성공
- [ ] 스크래퍼 테스트 성공

일일 리포트 생성 준비 완료! 🎉

