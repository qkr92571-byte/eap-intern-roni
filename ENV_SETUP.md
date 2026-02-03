# 환경 변수 설정 가이드

이 문서는 프로젝트 실행에 필요한 환경 변수를 설정하는 방법을 설명합니다.

## 📝 환경 변수 파일 생성

`backend/.env` 파일을 생성하고 아래 내용을 복사하여 실제 값으로 채워넣으세요.

```bash
cd backend
touch .env
# 또는
cp .env.example .env  # .env.example 파일이 있는 경우
```

## 🔑 필수 환경 변수

### Firebase 설정

```env
# Firebase 서비스 계정 키 파일 경로
# backend/config/ 디렉토리에 저장된 키 파일명을 지정
FIREBASE_CREDENTIALS_PATH=config/eap-intern-roni-firebase-adminsdk-fbsvc-52a59b23d2.json
```

**설정 방법**:
1. Firebase 콘솔 접속: https://console.firebase.google.com
2. 프로젝트 선택 또는 생성
3. 프로젝트 설정 > 서비스 계정 탭
4. "새 비공개 키 생성" 클릭하여 JSON 파일 다운로드
5. 다운로드한 파일을 `backend/config/` 디렉토리에 저장
6. 파일명을 `FIREBASE_CREDENTIALS_PATH`에 지정

---

### OpenAI API 설정

```env
# OpenAI API 키 (GPT 검수 기능 사용 시 필수)
# https://platform.openai.com/api-keys 에서 발급
OPENAI_API_KEY=sk-your-openai-api-key-here
```

**설정 방법**:
1. OpenAI 플랫폼 접속: https://platform.openai.com/api-keys
2. 로그인 후 "Create new secret key" 클릭
3. 생성된 키를 복사하여 `.env` 파일에 입력

---

### 프론트엔드 URL 설정

```env
# 프론트엔드 서버 주소 (슬랙 리포트의 링크에 사용됨)
FRONTEND_URL=http://172.30.1.17:3000
```

**설정 방법**:
- 로컬 개발: `http://localhost:3000`
- 사내 서버: 실제 IP 주소 사용 (예: `http://172.30.1.17:3000`)

---

## 🔔 선택 환경 변수 (슬랙 알림 사용 시)

### Slack 설정

```env
# Slack Bot Token
# https://api.slack.com/apps 에서 앱 생성 후 발급
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token-here

# Slack 채널 ID (공식 채널)
SLACK_CHANNEL_ID=C034EQD6W4W

# Slack 유저그룹 ID (EAP 파트 멘션용)
SLACK_EAP_USERGROUP=S08SE5ZTPQD
```

**설정 방법**:
1. Slack API 접속: https://api.slack.com/apps
2. "Create New App" 클릭
3. "OAuth & Permissions" 탭에서 Bot Token Scopes 추가:
   - `chat:write`
   - `chat:write.public`
   - `users:read`
4. "Install App to Workspace" 클릭하여 워크스페이스에 설치
5. 생성된 Bot Token을 복사하여 `.env` 파일에 입력
6. 채널에 Bot 초대: `/invite @봇이름`

---

## ⚙️ 선택 환경 변수 (기타)

### Flask 서버 설정

```env
# Flask 서버 포트 (기본값: 5000)
PORT=5000
```

---

### Playwright 설정

```env
# 브라우저 헤드리스 모드
# true: 백그라운드 실행 (서버 환경 권장)
# false: 브라우저 창 표시 (디버깅 시 유용)
PLAYWRIGHT_HEADLESS=true
```

---

### 나라장터 API 설정 (경쟁사 동향 수집 시)

```env
# 나라장터 공공데이터개방표준서비스 API 키
# https://www.data.go.kr 에서 발급
NARA_API_KEY=your-nara-api-key-here
```

---

### 코드 분석 및 최적화 에이전트 설정

```env
# 코드 분석 리포트 저장 디렉토리 (기본값: backend/code_analysis)
CODE_ANALYSIS_OUTPUT_DIR=backend/code_analysis

# 자동 수정 활성화 여부 (기본값: true)
AUTO_FIX_ENABLED=true

# 최적화용 AI 모델 (기본값: gpt-4o-mini)
OPTIMIZATION_MODEL=gpt-4o-mini

# 코드리뷰용 AI 모델 (기본값: gpt-4o-mini)
REVIEW_MODEL=gpt-4o-mini
```

**설정 방법**:
- `CODE_ANALYSIS_OUTPUT_DIR`: 분석 리포트가 저장될 디렉토리 경로
- `AUTO_FIX_ENABLED`: 코드 최적화 에이전트가 안전한 변경사항을 자동으로 적용할지 여부
- `OPTIMIZATION_MODEL`: 코드 최적화에 사용할 OpenAI 모델 (gpt-4o-mini, gpt-4 등)
- `REVIEW_MODEL`: 코드리뷰에 사용할 OpenAI 모델 (gpt-4o-mini, gpt-4 등)

---

## ✅ 환경 변수 확인

설정이 완료되었는지 확인하려면:

```bash
cd backend

# Python에서 환경 변수 확인
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()

required_vars = [
    'FIREBASE_CREDENTIALS_PATH',
    'OPENAI_API_KEY',
    'FRONTEND_URL'
]

print('환경 변수 확인:')
for var in required_vars:
    value = os.getenv(var)
    if value:
        # 민감한 정보는 일부만 표시
        if 'KEY' in var or 'TOKEN' in var:
            display_value = value[:10] + '...' if len(value) > 10 else value
        else:
            display_value = value
        print(f'  ✅ {var}: {display_value}')
    else:
        print(f'  ❌ {var}: 설정되지 않음')
"
```

---

## 🔒 보안 주의사항

⚠️ **중요**: `.env` 파일은 절대 Git에 커밋하지 마세요!

- `.gitignore`에 이미 포함되어 있습니다
- 환경 변수에는 민감한 정보(API 키, 토큰 등)가 포함됩니다
- 공유 시에는 `.env.example` 파일을 사용하세요

---

## 📚 관련 문서

- [QUICK_START.md](./QUICK_START.md) - 빠른 시작 가이드
- [WORKFLOW_GUIDE.md](./WORKFLOW_GUIDE.md) - 워크플로우 가이드
- [SETUP.md](./SETUP.md) - 상세 설치 가이드

