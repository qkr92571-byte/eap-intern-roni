@echo off
:: 어느 경로에서든 이 프로젝트의 Makefile을 실행하는 래퍼
:: setup.py 실행 후 PATH에 이 파일의 디렉토리가 등록되어 전역에서 동작합니다.
set PROJECT_DIR=%~dp0
cd /d %PROJECT_DIR%
make %*
