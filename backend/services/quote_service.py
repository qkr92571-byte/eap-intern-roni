"""
서비스 항목 추출 서비스
- 첨부파일에서 추출한 마크다운 파일을 분석하여 서비스 항목 추출
- ChatGPT API를 사용하여 서비스 구분 리스트 생성
- 마크다운 파일로 서비스 항목 리스트 저장
"""

import json
from pathlib import Path
from typing import List, Dict, Optional

from utils.openai_client import get_openai_client
from utils.constants import (
    OPENAI_MODEL_SERVICE_EXTRACTION,
    OPENAI_MAX_TOKENS_SERVICE_EXTRACTION,
    OPENAI_TEMPERATURE_SERVICE_EXTRACTION
)

# 프로젝트 루트 디렉토리
PROJECT_ROOT = Path(__file__).parent.parent
TEMPLATE_DIR = PROJECT_ROOT / "downloads" / "template"
TEMPLATE_PATH = TEMPLATE_DIR / "eap_template.xlsx"


def read_markdown_files(announcement_dir: Path) -> List[str]:
    """
    공고 디렉토리에서 마크다운 파일들을 읽어서 텍스트 반환
    
    Args:
        announcement_dir: 공고 디렉토리 경로 (예: downloads/20251201/R25BK01187770-000/)
    
    Returns:
        마크다운 파일 내용 리스트
    """
    markdown_files = list(announcement_dir.glob("*.md"))
    contents = []
    
    for md_file in markdown_files:
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
                contents.append(f"=== {md_file.name} ===\n{content}")
        except Exception as e:
            print(f"마크다운 파일 읽기 실패 ({md_file}): {e}")
    
    return contents


def extract_service_items_with_chatgpt(markdown_contents: List[str]) -> List[Dict[str, str]]:
    """
    ChatGPT API를 사용하여 마크다운 파일에서 서비스 항목 추출
    
    Args:
        markdown_contents: 마크다운 파일 내용 리스트
    
    Returns:
        서비스 항목 리스트 [{"구분": "서비스명", "설명": "..."}, ...]
    """
    try:
        # 공통 OpenAI 클라이언트 사용
        client = get_openai_client()
        
        # 마크다운 내용 합치기
        combined_content = "\n\n".join(markdown_contents)
        
        # 프롬프트 작성
        prompt = f"""
다음은 공고 문서에서 추출한 내용입니다. 이 사업에서 요구하는 서비스 항목들을 추출하여 리스트로 만들어주세요.

문서 내용:
{combined_content[:15000]}  # 토큰 제한을 고려하여 일부만 전송

요구사항:
1. 이 사업에서 실제로 수행해야 하는 서비스 항목들을 구분하여 나열해주세요.
2. 각 서비스 항목은 명확하고 구체적인 이름으로 작성해주세요.
3. 각 서비스 항목에 대한 간단한 설명도 포함해주세요.

응답 형식 (JSON):
{{
  "service_items": [
    {{
      "구분": "서비스 항목명",
      "설명": "서비스에 대한 간단한 설명"
    }},
    ...
  ]
}}

예시:
{{
  "service_items": [
    {{
      "구분": "1:1 개인 심리상담",
      "설명": "소방공무원 대상 개인 심리상담 서비스 제공"
    }},
    {{
      "구분": "집단 상담 프로그램",
      "설명": "팀 단위 집단 심리상담 프로그램 운영"
    }},
    {{
      "구분": "정신건강 교육",
      "설명": "소방관서 방문을 통한 정신건강 교육 실시"
    }}
  ]
}}

중요: JSON 형식으로만 응답하고, 다른 설명은 포함하지 마세요.
"""
        
        response = client.chat.completions.create(
            model=OPENAI_MODEL_SERVICE_EXTRACTION,
            messages=[
                {"role": "system", "content": "당신은 공고 문서를 분석하여 서비스 항목을 추출하는 전문가입니다. 정확하고 구조화된 JSON 형식으로 응답합니다."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=OPENAI_MAX_TOKENS_SERVICE_EXTRACTION,
            temperature=OPENAI_TEMPERATURE_SERVICE_EXTRACTION
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # JSON 파싱 시도 (응답이 JSON 형식인지 확인)
        try:
            # JSON 코드 블록 제거 (```json ... ``` 형식)
            if result_text.startswith("```"):
                # 첫 번째 ``` 이후부터 마지막 ``` 이전까지 추출
                start_idx = result_text.find("```") + 3
                if result_text[start_idx:start_idx+4].lower() == "json":
                    start_idx += 4
                end_idx = result_text.rfind("```")
                if end_idx > start_idx:
                    result_text = result_text[start_idx:end_idx].strip()
            
            result = json.loads(result_text)
            service_items = result.get("service_items", [])
        except json.JSONDecodeError:
            # JSON 파싱 실패 시 텍스트에서 직접 추출 시도
            print(f"JSON 파싱 실패, 원본 응답:\n{result_text}")
            service_items = []
        
        return service_items
        
    except json.JSONDecodeError as e:
        print(f"JSON 파싱 오류: {e}")
        print(f"응답 내용: {result_text}")
        return []
    except Exception as e:
        print(f"ChatGPT API 호출 오류: {str(e)}")
        import traceback
        traceback.print_exc()
        return []


def save_service_items_to_markdown(
    output_path: Path,
    service_items: List[Dict[str, str]],
    announcement_info: Optional[Dict] = None
) -> bool:
    """
    서비스 항목을 마크다운 파일로 저장
    
    Args:
        output_path: 출력 마크다운 파일 경로
        service_items: 서비스 항목 리스트
        announcement_info: 공고 정보 (사업명, 주관기관 등)
    
    Returns:
        성공 여부
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            # 헤더 작성
            f.write("# 서비스 항목 리스트\n\n")
            
            # 공고 정보 작성
            if announcement_info:
                f.write("## 공고 정보\n\n")
                if 'title' in announcement_info:
                    f.write(f"- **사업명**: {announcement_info['title']}\n")
                if 'agency' in announcement_info:
                    f.write(f"- **주관기관**: {announcement_info['agency']}\n")
                f.write("\n---\n\n")
            
            # 서비스 항목 작성
            f.write("## 요구 서비스 항목\n\n")
            
            for idx, item in enumerate(service_items, 1):
                구분 = item.get('구분', '')
                설명 = item.get('설명', '')
                
                f.write(f"### {idx}. {구분}\n\n")
                if 설명:
                    f.write(f"{설명}\n\n")
                f.write("---\n\n")
        
        print(f"서비스 항목 리스트 저장 완료: {output_path}")
        return True
        
    except Exception as e:
        print(f"마크다운 파일 생성 오류: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def generate_service_list(
    announcement_number: str,
    announcement_info: Optional[Dict] = None
) -> Dict:
    """
    서비스 항목 리스트 생성 메인 함수
    
    Args:
        announcement_number: 공고번호
        announcement_info: 공고 정보 (title, agency 등)
    
    Returns:
        {
            "success": bool,
            "output_path": str,
            "service_items": List[Dict],
            "error": Optional[str]
        }
    """
    try:
        # 공고 디렉토리 찾기
        downloads_dir = PROJECT_ROOT / "downloads"
        announcement_dir = None
        
        # 날짜별 폴더에서 공고 디렉토리 찾기
        for date_dir in downloads_dir.iterdir():
            if date_dir.is_dir() and date_dir.name.isdigit():
                potential_dir = date_dir / announcement_number
                if potential_dir.exists():
                    announcement_dir = potential_dir
                    break
        
        if not announcement_dir or not announcement_dir.exists():
            return {
                "success": False,
                "error": f"공고 디렉토리를 찾을 수 없습니다: {announcement_number}",
                "service_items": []
            }
        
        # 마크다운 파일 읽기
        markdown_contents = read_markdown_files(announcement_dir)
        if not markdown_contents:
            return {
                "success": False,
                "error": "마크다운 파일을 찾을 수 없습니다.",
                "service_items": []
            }
        
        # ChatGPT로 서비스 항목 추출
        service_items = extract_service_items_with_chatgpt(markdown_contents)
        if not service_items:
            return {
                "success": False,
                "error": "서비스 항목을 추출할 수 없습니다.",
                "service_items": []
            }
        
        # 출력 경로 설정
        output_filename = f"service_list_{announcement_number}.md"
        output_path = announcement_dir / output_filename
        
        # 마크다운 파일 생성
        success = save_service_items_to_markdown(
            output_path,
            service_items,
            announcement_info
        )
        
        if success:
            return {
                "success": True,
                "output_path": str(output_path),
                "service_items": service_items,
                "error": None
            }
        else:
            return {
                "success": False,
                "error": "마크다운 파일 생성 실패",
                "service_items": service_items
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"서비스 항목 리스트 생성 중 오류: {str(e)}",
            "service_items": []
        }

