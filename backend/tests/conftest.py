"""
pytest 공통 픽스처 및 설정
"""
import sys
from pathlib import Path

# backend 디렉토리를 Python path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))
