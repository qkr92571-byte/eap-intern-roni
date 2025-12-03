"""
파일 파싱 서비스
- PDF 파일 파싱 (pdfplumber)
- HWP 파일 파싱 (pyhwp)
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

# PDF 파싱
try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False
    logger.warning("⚠️  pdfplumber가 설치되지 않았습니다. PDF 파싱이 불가능합니다.")

# HWP 파싱
try:
    from pyhwp import hwp5
    from pyhwp.hwp5 import plat
    HAS_PYHWP = True
except ImportError:
    HAS_PYHWP = False
    logger.warning("⚠️  pyhwp가 설치되지 않았습니다. HWP 파싱이 불가능합니다.")


def parse_pdf(file_path: str) -> Dict[str, Any]:
    """
    PDF 파일에서 텍스트 및 표 추출
    
    Args:
        file_path: PDF 파일 경로
    
    Returns:
        {
            'text': str,  # 추출된 텍스트
            'tables': List[List],  # 추출된 표 리스트
            'page_count': int,  # 페이지 수
            'success': bool,
            'error': Optional[str]
        }
    """
    if not HAS_PDFPLUMBER:
        return {
            'text': '',
            'tables': [],
            'page_count': 0,
            'success': False,
            'error': 'pdfplumber가 설치되지 않았습니다.'
        }
    
    if not os.path.exists(file_path):
        return {
            'text': '',
            'tables': [],
            'page_count': 0,
            'success': False,
            'error': f'파일을 찾을 수 없습니다: {file_path}'
        }
    
    try:
        text_content = []
        all_tables = []
        page_count = 0
        
        with pdfplumber.open(file_path) as pdf:
            page_count = len(pdf.pages)
            
            for page_num, page in enumerate(pdf.pages, 1):
                # 텍스트 추출
                text = page.extract_text()
                if text:
                    text_content.append(f"=== 페이지 {page_num} ===\n{text}")
                
                # 표 추출
                tables = page.extract_tables()
                if tables:
                    for table_num, table in enumerate(tables, 1):
                        all_tables.append({
                            'page': page_num,
                            'table_num': table_num,
                            'data': table
                        })
        
        return {
            'text': '\n\n'.join(text_content),
            'tables': all_tables,
            'page_count': page_count,
            'success': True,
            'error': None
        }
    
    except Exception as e:
        logger.error(f"PDF 파싱 중 오류 발생: {str(e)}")
        return {
            'text': '',
            'tables': [],
            'page_count': 0,
            'success': False,
            'error': f'PDF 파싱 실패: {str(e)}'
        }


def parse_hwpx(file_path: str) -> Dict[str, Any]:
    """
    HWPX 파일에서 텍스트 추출 (ZIP 압축 XML 형식)
    
    Args:
        file_path: HWPX 파일 경로
    
    Returns:
        {
            'text': str,  # 추출된 텍스트
            'success': bool,
            'error': Optional[str],
            'format': str  # 'hwpx'
        }
    """
    import zipfile
    import xml.etree.ElementTree as ET
    
    if not os.path.exists(file_path):
        return {
            'text': '',
            'success': False,
            'error': f'파일을 찾을 수 없습니다: {file_path}',
            'format': 'unknown'
        }
    
    try:
        text_content = []
        
        # HWPX는 ZIP 파일이므로 압축 해제
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            # Contents/section0.xml 파일에서 텍스트 추출
            try:
                if 'Contents/section0.xml' in zip_ref.namelist():
                    xml_content = zip_ref.read('Contents/section0.xml')
                    root = ET.fromstring(xml_content)
                    
                    # XML에서 텍스트 추출
                    # HWPX의 텍스트는 <t> 태그에 있음
                    for t_elem in root.iter():
                        if t_elem.tag.endswith('}t') or t_elem.tag == 't':
                            text = t_elem.text
                            if text and text.strip():
                                text_content.append(text.strip())
                    
                    # 네임스페이스 처리
                    if not text_content:
                        # 네임스페이스가 있는 경우
                        namespaces = {'hwp': 'http://www.hancom.co.kr/hwpml/2011'}
                        for t_elem in root.findall('.//hwp:t', namespaces):
                            text = t_elem.text
                            if text and text.strip():
                                text_content.append(text.strip())
                
                # 다른 섹션도 확인
                for name in zip_ref.namelist():
                    if name.startswith('Contents/section') and name.endswith('.xml'):
                        if name != 'Contents/section0.xml':
                            try:
                                xml_content = zip_ref.read(name)
                                root = ET.fromstring(xml_content)
                                for t_elem in root.iter():
                                    if t_elem.tag.endswith('}t') or t_elem.tag == 't':
                                        text = t_elem.text
                                        if text and text.strip():
                                            text_content.append(text.strip())
                            except:
                                continue
            except Exception as e:
                logger.warning(f"HWPX XML 파싱 중 오류: {str(e)}")
        
        final_text = '\n\n'.join(text_content) if text_content else ''
        
        return {
            'text': final_text,
            'success': len(text_content) > 0,
            'error': None if len(text_content) > 0 else '텍스트를 추출할 수 없습니다.',
            'format': 'hwpx'
        }
    
    except zipfile.BadZipFile:
        return {
            'text': '',
            'success': False,
            'error': 'ZIP 파일 형식이 올바르지 않습니다.',
            'format': 'unknown'
        }
    except Exception as e:
        logger.error(f"HWPX 파싱 중 오류 발생: {str(e)}")
        return {
            'text': '',
            'success': False,
            'error': f'HWPX 파싱 실패: {str(e)}',
            'format': 'unknown'
        }


def parse_hwp(file_path: str) -> Dict[str, Any]:
    """
    HWP 파일에서 텍스트 추출 (HWP5 형식)
    HWPX 파일인 경우 parse_hwpx()를 호출
    
    Args:
        file_path: HWP 파일 경로
    
    Returns:
        {
            'text': str,  # 추출된 텍스트
            'success': bool,
            'error': Optional[str],
            'format': str  # 'hwp5', 'hwpx', or 'unknown'
        }
    """
    # 파일 확장자 확인
    file_ext = Path(file_path).suffix.lower()
    
    # HWPX 파일인 경우 별도 처리
    if file_ext == '.hwpx':
        return parse_hwpx(file_path)
    
    if not HAS_PYHWP:
        return {
            'text': '',
            'success': False,
            'error': 'pyhwp가 설치되지 않았습니다.',
            'format': 'unknown'
        }
    
    if not os.path.exists(file_path):
        return {
            'text': '',
            'success': False,
            'error': f'파일을 찾을 수 없습니다: {file_path}',
            'format': 'unknown'
        }
    
    try:
        # HWP5 파일 열기
        hwp_file = hwp5.open(file_path)
        
        text_content = []
        
        # 본문 텍스트 추출
        try:
            # HWP5 구조: bodytext.sections -> paragraphs
            if hasattr(hwp_file, 'bodytext') and hwp_file.bodytext:
                for section in hwp_file.bodytext.sections:
                    if hasattr(section, 'paragraphs'):
                        for paragraph in section.paragraphs:
                            # 텍스트 추출 시도
                            try:
                                if hasattr(paragraph, 'get_text'):
                                    text = paragraph.get_text()
                                elif hasattr(paragraph, 'text'):
                                    text = paragraph.text
                                else:
                                    # 다른 방법으로 텍스트 추출 시도
                                    text = str(paragraph)
                                
                                if text and text.strip():
                                    text_content.append(text.strip())
                            except Exception as e:
                                logger.debug(f"단락 텍스트 추출 실패: {str(e)}")
                                continue
        except Exception as e:
            logger.warning(f"본문 텍스트 추출 중 오류: {str(e)}")
        
        # 텍스트가 없으면 다른 방법 시도
        if not text_content:
            try:
                # HWP5의 다른 구조 시도
                # BinData나 다른 섹션에서 텍스트 추출
                for section_name in dir(hwp_file):
                    if 'text' in section_name.lower() or 'content' in section_name.lower():
                        try:
                            section = getattr(hwp_file, section_name)
                            if hasattr(section, '__iter__'):
                                for item in section:
                                    if hasattr(item, 'get_text'):
                                        text = item.get_text()
                                        if text:
                                            text_content.append(text)
                        except:
                            continue
            except Exception as e:
                logger.debug(f"대체 텍스트 추출 방법 실패: {str(e)}")
        
        # 최종 텍스트 조합
        final_text = '\n\n'.join(text_content) if text_content else ''
        
        return {
            'text': final_text,
            'success': len(text_content) > 0,
            'error': None if len(text_content) > 0 else '텍스트를 추출할 수 없습니다.',
            'format': 'hwp5'
        }
    
    except Exception as e:
        error_msg = str(e)
        logger.error(f"HWP 파싱 중 오류 발생: {error_msg}")
        
        # HWP5가 아닌 경우 감지
        if 'not a valid HWP5' in error_msg.lower() or 'hwp5' not in error_msg.lower():
            return {
                'text': '',
                'success': False,
                'error': f'HWP5 형식이 아닙니다. 구버전 HWP 파일일 수 있습니다: {error_msg}',
                'format': 'unknown'
            }
        
        return {
            'text': '',
            'success': False,
            'error': f'HWP 파싱 실패: {error_msg}',
            'format': 'unknown'
        }


def parse_file(file_path: str) -> Dict[str, Any]:
    """
    파일 확장자에 따라 자동으로 적절한 파서 선택
    
    Args:
        file_path: 파일 경로
    
    Returns:
        파싱 결과 딕셔너리
    """
    if not os.path.exists(file_path):
        return {
            'text': '',
            'tables': [],
            'success': False,
            'error': f'파일을 찾을 수 없습니다: {file_path}',
            'file_type': 'unknown'
        }
    
    file_ext = Path(file_path).suffix.lower()
    
    if file_ext == '.pdf':
        result = parse_pdf(file_path)
        result['file_type'] = 'pdf'
        return result
    
    elif file_ext in ['.hwp', '.hwpx']:
        result = parse_hwp(file_path)  # parse_hwp가 내부에서 HWPX 감지하여 처리
        result['file_type'] = 'hwp' if result.get('format') == 'hwp5' else 'hwpx'
        # HWP/HWPX는 표 추출이 어려우므로 빈 리스트 반환
        if 'tables' not in result:
            result['tables'] = []
        return result
    
    else:
        return {
            'text': '',
            'tables': [],
            'success': False,
            'error': f'지원하지 않는 파일 형식입니다: {file_ext}',
            'file_type': file_ext
        }


def get_supported_formats() -> List[str]:
    """
    지원하는 파일 형식 목록 반환
    
    Returns:
        지원하는 파일 확장자 리스트 (예: ['.pdf', '.hwp', '.hwpx'])
    """
    formats = []
    
    if HAS_PDFPLUMBER:
        formats.append('.pdf')
    
    # HWP5는 pyhwp 필요
    if HAS_PYHWP:
        formats.append('.hwp')
    
    # HWPX는 ZIP/XML 파싱으로 지원 (pyhwp 불필요)
    formats.append('.hwpx')
    
    return formats

