"""
EAP 인턴로니 시스템 설치 스크립트
실행: python setup.py
"""
import subprocess
import sys
import os

def run(cmd, **kwargs):
    print(f"  > {' '.join(str(c) for c in cmd)}")
    subprocess.run(cmd, check=True, **kwargs)

def install_make_windows():
    """Windows에서 winget으로 make 설치"""
    try:
        subprocess.run(["make", "--version"], capture_output=True, check=True)
        print("  make 이미 설치되어 있습니다.")
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("  winget으로 make 설치 중...")
        subprocess.run(
            ["winget", "install", "--id", "GnuWin32.Make", "-e", "--silent"],
            check=False
        )

def register_path_windows():
    """프로젝트 경로를 Windows 사용자 PATH에 등록"""
    import winreg
    import ctypes

    project_dir = os.path.dirname(os.path.abspath(__file__))
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_ALL_ACCESS
        )
        current_path, _ = winreg.QueryValueEx(key, "PATH")
        if project_dir.lower() not in current_path.lower():
            new_path = current_path.rstrip(";") + ";" + project_dir
            winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ, new_path)
            # 환경변수 변경 즉시 반영
            ctypes.windll.user32.SendMessageW(0xFFFF, 0x001A, 0, "Environment")
            print(f"  PATH 등록 완료: {project_dir}")
        else:
            print(f"  이미 PATH에 등록되어 있습니다: {project_dir}")
        winreg.CloseKey(key)
    except Exception as e:
        print(f"  PATH 자동 등록 실패 ({e})")
        print(f"  수동으로 PATH에 추가하세요: {project_dir}")

# ── 1단계: 백엔드 의존성 ──────────────────────────────────
print("\n[1/4] 백엔드 패키지 설치 중...")
run([sys.executable, "-m", "pip", "install", "-r", "backend/requirements.txt"])

# ── 2단계: Playwright 브라우저 ────────────────────────────
print("\n[2/4] Playwright 브라우저(Chromium) 설치 중...")
run([sys.executable, "-m", "playwright", "install", "chromium"])

# ── 3단계: 프론트엔드 의존성 ──────────────────────────────
print("\n[3/4] 프론트엔드 패키지 설치 중...")
npm = "npm.cmd" if sys.platform == "win32" else "npm"
run([npm, "install"], cwd="frontend")

# ── 4단계: Windows 전용 설정 ─────────────────────────────
if sys.platform == "win32":
    print("\n[4/4] Windows 환경 설정 중...")
    install_make_windows()
    register_path_windows()
else:
    print("\n[4/4] Windows가 아닌 환경 — PATH 등록 생략")

# ── 완료 안내 ─────────────────────────────────────────────
print("\n" + "="*50)
print("설치 완료!")
print("="*50)
print()
print("다음 단계:")
print("  1. backend/.env 파일 생성")
print("     (.env.example 파일을 복사한 후 값을 채우세요)")
print()
print("  2. CMD를 새로 열고 아래 명령어 실행:")
print("     make daily")
print()
