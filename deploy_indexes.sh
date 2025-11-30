#!/bin/bash
# Firestore 인덱스 배포 스크립트

echo "=========================================="
echo "Firestore 인덱스 배포"
echo "=========================================="
echo ""

# 프로젝트 디렉토리로 이동
cd "$(dirname "$0")"

# Firebase 로그인 확인
echo "1. Firebase 로그인 상태 확인 중..."
if ! firebase projects:list &>/dev/null; then
    echo "   ⚠️  Firebase에 로그인되어 있지 않습니다."
    echo "   다음 명령어를 실행하여 로그인하세요:"
    echo "   firebase login"
    echo ""
    exit 1
fi

echo "   ✅ Firebase 로그인 확인됨"
echo ""

# 프로젝트 설정 확인
echo "2. 프로젝트 설정 확인 중..."
if [ ! -f ".firebaserc" ]; then
    echo "   ⚠️  .firebaserc 파일이 없습니다."
    exit 1
fi

if [ ! -f "firebase.json" ]; then
    echo "   ⚠️  firebase.json 파일이 없습니다."
    exit 1
fi

if [ ! -f "firestore.indexes.json" ]; then
    echo "   ⚠️  firestore.indexes.json 파일이 없습니다."
    exit 1
fi

echo "   ✅ 설정 파일 확인 완료"
echo ""

# 프로젝트 선택
echo "3. 프로젝트 선택 중..."
firebase use eap-intern-roni
if [ $? -ne 0 ]; then
    echo "   ⚠️  프로젝트 선택 실패"
    exit 1
fi

echo "   ✅ 프로젝트 선택 완료: eap-intern-roni"
echo ""

# 인덱스 배포
echo "4. 인덱스 배포 중..."
echo "   (이 작업은 몇 분이 걸릴 수 있습니다)"
echo ""
firebase deploy --only firestore:indexes

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✅ 인덱스 배포 완료!"
    echo "=========================================="
    echo ""
    echo "인덱스 생성 상태 확인:"
    echo "https://console.firebase.google.com/project/eap-intern-roni/firestore/indexes"
else
    echo ""
    echo "=========================================="
    echo "❌ 인덱스 배포 실패"
    echo "=========================================="
    exit 1
fi


