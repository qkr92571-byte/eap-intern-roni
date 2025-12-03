#!/usr/bin/env python3
"""
파일 파서 테스트 스크립트
- PDF 파일 파싱 테스트
- HWP 파일 파싱 테스트
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from services.file_parser_service import parse_pdf, parse_hwp, parse_file, get_supported_formats

def test_pdf_parsing(file_path: str):
    """PDF 파일 파싱 테스트"""
    print("=" * 60)
    print("PDF 파싱 테스트")
    print("=" * 60)
    print(f"파일: {file_path}")
    print()
    
    if not os.path.exists(file_path):
        print(f"❌ 파일을 찾을 수 없습니다: {file_path}")
        return False
    
    result = parse_pdf(file_path)
    
    if result['success']:
        print(f"✅ 파싱 성공!")
        print(f"   페이지 수: {result['page_count']}")
        print(f"   텍스트 길이: {len(result['text'])} 문자")
        print(f"   표 개수: {len(result['tables'])}")
        print()
        print("텍스트 미리보기 (처음 500자):")
        print("-" * 60)
        print(result['text'][:500])
        if len(result['text']) > 500:
            print("...")
        print("-" * 60)
        return True
    else:
        print(f"❌ 파싱 실패: {result.get('error', '알 수 없는 오류')}")
        return False

def test_hwp_parsing(file_path: str):
    """HWP 파일 파싱 테스트"""
    print("=" * 60)
    print("HWP 파싱 테스트")
    print("=" * 60)
    print(f"파일: {file_path}")
    print()
    
    if not os.path.exists(file_path):
        print(f"❌ 파일을 찾을 수 없습니다: {file_path}")
        return False
    
    result = parse_hwp(file_path)
    
    if result['success']:
        print(f"✅ 파싱 성공!")
        print(f"   형식: {result.get('format', 'unknown')}")
        print(f"   텍스트 길이: {len(result['text'])} 문자")
        print()
        print("텍스트 미리보기 (처음 500자):")
        print("-" * 60)
        print(result['text'][:500])
        if len(result['text']) > 500:
            print("...")
        print("-" * 60)
        return True
    else:
        print(f"❌ 파싱 실패: {result.get('error', '알 수 없는 오류')}")
        print(f"   형식: {result.get('format', 'unknown')}")
        return False

def test_auto_parsing(file_path: str):
    """자동 파일 형식 감지 및 파싱 테스트"""
    print("=" * 60)
    print("자동 파싱 테스트")
    print("=" * 60)
    print(f"파일: {file_path}")
    print()
    
    if not os.path.exists(file_path):
        print(f"❌ 파일을 찾을 수 없습니다: {file_path}")
        return False
    
    result = parse_file(file_path)
    
    print(f"감지된 파일 형식: {result.get('file_type', 'unknown')}")
    
    if result['success']:
        print(f"✅ 파싱 성공!")
        print(f"   텍스트 길이: {len(result.get('text', ''))} 문자")
        if 'page_count' in result:
            print(f"   페이지 수: {result['page_count']}")
        if 'tables' in result:
            print(f"   표 개수: {len(result['tables'])}")
        print()
        print("텍스트 미리보기 (처음 500자):")
        print("-" * 60)
        text = result.get('text', '')
        print(text[:500])
        if len(text) > 500:
            print("...")
        print("-" * 60)
        return True
    else:
        print(f"❌ 파싱 실패: {result.get('error', '알 수 없는 오류')}")
        return False

def main():
    """메인 함수"""
    print("파일 파서 테스트 스크립트")
    print()
    
    # 지원하는 형식 확인
    supported = get_supported_formats()
    print(f"지원하는 파일 형식: {', '.join(supported) if supported else '없음'}")
    print()
    
    if len(sys.argv) < 2:
        print("사용법:")
        print(f"  python {sys.argv[0]} <파일경로>")
        print()
        print("예시:")
        print(f"  python {sys.argv[0]} test.pdf")
        print(f"  python {sys.argv[0]} test.hwp")
        return
    
    file_path = sys.argv[1]
    file_ext = Path(file_path).suffix.lower()
    
    if file_ext == '.pdf':
        test_pdf_parsing(file_path)
    elif file_ext in ['.hwp', '.hwpx']:
        test_hwp_parsing(file_path)
    else:
        # 자동 감지
        test_auto_parsing(file_path)

if __name__ == "__main__":
    main()

