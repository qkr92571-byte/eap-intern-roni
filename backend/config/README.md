# Firebase 설정 디렉토리

이 디렉토리에 Firebase 서비스 계정 키 파일을 저장하세요.

## 설정 방법

1. Firebase 콘솔 (https://console.firebase.google.com) 접속
2. 프로젝트 선택 또는 새 프로젝트 생성
3. 프로젝트 설정 > 서비스 계정 탭으로 이동
4. "새 비공개 키 생성" 클릭하여 JSON 파일 다운로드
5. 다운로드한 파일을 이 디렉토리에 `firebase-credentials.json` 이름으로 저장

## 보안 주의사항

⚠️ **중요**: 이 파일은 절대 Git에 커밋하지 마세요!
- `.gitignore`에 이미 포함되어 있습니다
- 파일명이 `firebase-credentials.json` 또는 `firebase-adminsdk-*.json` 형식이면 자동으로 제외됩니다

## 파일 구조 예시

```
backend/
├── config/
│   ├── firebase-credentials.json  # 여기에 Firebase 키 파일 저장
│   └── README.md
└── .env                           # FIREBASE_CREDENTIALS_PATH 설정
```


