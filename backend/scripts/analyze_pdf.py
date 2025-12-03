"""
정성제안서 PDF를 페이지별로 분석하여 Markdown 파일로 변환하는 스크립트
"""
import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import pdfplumber
    USE_PDFPLUMBER = True
except ImportError:
    try:
        import PyPDF2
        USE_PDFPLUMBER = False
    except ImportError:
        print("PDF 라이브러리가 설치되어 있지 않습니다.")
        print("다음 명령어로 설치해주세요: pip install pdfplumber")
        sys.exit(1)

def extract_text_with_pdfplumber(pdf_path):
    """pdfplumber를 사용하여 PDF 텍스트 추출"""
    text_by_page = []
    
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        print(f"총 {total_pages}페이지 발견")
        
        for page_num, page in enumerate(pdf.pages, 1):
            print(f"페이지 {page_num}/{total_pages} 처리 중...")
            
            # 텍스트 추출
            text = page.extract_text()
            
            # 테이블 추출 시도
            tables = page.extract_tables()
            
            page_data = {
                'page_number': page_num,
                'text': text or '',
                'tables': tables or []
            }
            
            text_by_page.append(page_data)
    
    return text_by_page

def extract_text_with_pypdf2(pdf_path):
    """PyPDF2를 사용하여 PDF 텍스트 추출"""
    text_by_page = []
    
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        total_pages = len(pdf_reader.pages)
        print(f"총 {total_pages}페이지 발견")
        
        for page_num in range(total_pages):
            print(f"페이지 {page_num + 1}/{total_pages} 처리 중...")
            page = pdf_reader.pages[page_num]
            text = page.extract_text()
            
            page_data = {
                'page_number': page_num + 1,
                'text': text or '',
                'tables': []
            }
            
            text_by_page.append(page_data)
    
    return text_by_page

def format_table_as_markdown(table):
    """테이블을 Markdown 형식으로 변환"""
    if not table or len(table) == 0:
        return ""
    
    markdown = "\n"
    # 헤더
    if len(table) > 0:
        header = "| " + " | ".join(str(cell) if cell else "" for cell in table[0]) + " |"
        markdown += header + "\n"
        markdown += "| " + " | ".join(["---"] * len(table[0])) + " |\n"
    
    # 데이터 행
    for row in table[1:]:
        markdown += "| " + " | ".join(str(cell) if cell else "" for cell in row) + " |\n"
    
    return markdown

def create_markdown_analysis(pdf_path, output_path):
    """PDF를 분석하여 Markdown 파일 생성"""
    print(f"PDF 파일 읽기: {pdf_path}")
    
    # PDF 텍스트 추출
    if USE_PDFPLUMBER:
        pages_data = extract_text_with_pdfplumber(pdf_path)
    else:
        pages_data = extract_text_with_pypdf2(pdf_path)
    
    # Markdown 파일 생성
    print(f"\nMarkdown 파일 생성: {output_path}")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# 정성제안서 원본 분석\n\n")
        f.write(f"**원본 파일**: `{os.path.basename(pdf_path)}`\n\n")
        f.write(f"**총 페이지 수**: {len(pages_data)}페이지\n\n")
        f.write("---\n\n")
        
        for page_data in pages_data:
            page_num = page_data['page_number']
            text = page_data['text']
            tables = page_data['tables']
            
            f.write(f"## 페이지 {page_num}\n\n")
            
            # 텍스트 내용
            if text and text.strip():
                f.write("### 텍스트 내용\n\n")
                # 텍스트를 문단별로 정리
                paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
                for para in paragraphs:
                    f.write(f"{para}\n\n")
            
            # 테이블 내용
            if tables and len(tables) > 0:
                f.write("### 테이블 내용\n\n")
                for i, table in enumerate(tables, 1):
                    f.write(f"#### 테이블 {i}\n\n")
                    f.write(format_table_as_markdown(table))
                    f.write("\n")
            
            f.write("---\n\n")
    
    print(f"✅ Markdown 파일 생성 완료: {output_path}")

if __name__ == "__main__":
    # 파일 경로 설정
    config_dir = project_root / "config"
    pdf_path = config_dir / "정성제안서_원본.pdf"
    output_path = config_dir / "정성제안서_원본_분석.md"
    
    if not pdf_path.exists():
        print(f"❌ PDF 파일을 찾을 수 없습니다: {pdf_path}")
        sys.exit(1)
    
    create_markdown_analysis(pdf_path, output_path)
    print("\n✅ 분석 완료!")

