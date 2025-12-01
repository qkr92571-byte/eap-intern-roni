#!/bin/bash

# 나라장터 공고 시스템 프론트엔드 빌드 + Firebase Hosting 배포 스크립트
# 사용법:
#   chmod +x deploy_frontend.sh   # 최초 1회
#   ./deploy_frontend.sh          # 이후 매번 빌드 + 배포 한 번에 실행

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "✅ 프론트엔드 빌드 시작..."
cd "$PROJECT_ROOT/frontend"
npm run build

echo "✅ Firebase Hosting 배포 시작..."
cd "$PROJECT_ROOT"
firebase deploy --only hosting

echo "🎉 프론트엔드 빌드 및 Firebase Hosting 배포 완료!"


