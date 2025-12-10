"""
나라장터 공고 상세 페이지 첨부파일 수집 및 내용 확인 서비스

- Playwright로 상세 페이지 접근
- 첨부파일 테이블에서 파일 다운로드
- pdf/docx 텍스트 추출 (기타 형식은 추출 불가 시 메시지 제공)
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import os
import re
import zipfile

from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv()

# 프로젝트 루트 기준 다운로드 디렉토리
PROJECT_ROOT = Path(__file__).parent.parent
DOWNLOAD_DIR = PROJECT_ROOT / "downloads"


def sanitize_filename(name: str) -> str:
    """파일 시스템 안전한 이름으로 변환"""
    # Windows/Mac/Linux에서 문제가 되는 문자 제거
    invalid_chars = r'[<>:"/\\|?*\x00-\x1f]'
    name = re.sub(invalid_chars, '_', name)
    # 연속된 공백/언더스코어 정리
    name = re.sub(r'[_\s]+', '_', name)
    # 앞뒤 공백/언더스코어 제거
    name = name.strip('_').strip()
    # 빈 문자열이면 기본값
    if not name:
        name = "unnamed"
    # 길이 제한 (파일 시스템 제한 고려)
    if len(name) > 200:
        name = name[:200]
    return name


def get_announcement_info(announcement_number: str) -> Optional[Dict]:
    """리포트 파일에서 공고 정보 조회"""
    from services.file_service import load_report
    
    # 최근 30일 리포트 파일에서 검색
    for days_back in range(30):
        check_date = datetime.now() - timedelta(days=days_back)
        report_data = load_report(check_date)
        if not report_data or not isinstance(report_data, list):
            continue
        
        for ann in report_data:
            if not isinstance(ann, dict):
                continue
            if ann.get('announcement_number') == announcement_number:
                return ann
    
    return None


def ensure_download_dir(announcement_number: str, title: Optional[str] = None, created_at: Optional[str] = None) -> Path:
    """
    날짜별 다운로드 디렉토리 생성
    
    구조: downloads/YYYYMMDD/{공고번호}/
    """
    # 날짜 추출 (created_at 또는 오늘)
    date_str = None
    if created_at:
        try:
            dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            date_str = dt.strftime('%Y%m%d')
        except Exception:
            pass
    
    if not date_str:
        date_str = datetime.now().strftime('%Y%m%d')
    
    # 경로 생성: downloads/YYYYMMDD/{공고번호}/
    target_dir = DOWNLOAD_DIR / date_str / announcement_number
    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir


def build_detail_url(announcement_number: str, bid_ord: str = "000") -> str:
    """공고번호로 나라장터 상세 URL 생성"""
    parts = announcement_number.split("-")
    bid_pbanc_no = parts[0]
    bid_pbanc_ord = parts[1] if len(parts) > 1 and parts[1] else bid_ord
    return f"https://www.g2b.go.kr/link/PNPE027_01/single/?bidPbancNo={bid_pbanc_no}&bidPbancOrd={bid_pbanc_ord}"


def download_attachments(
    announcement_number: str,
    bid_ord: str = "000",
    headless: Optional[bool] = None,
    title: Optional[str] = None,
    created_at: Optional[str] = None,
) -> Dict:
    """
    공고 상세 페이지에서 첨부파일 다운로드
    
    Args:
        announcement_number: 공고번호
        bid_ord: 입찰차수 (기본값: "000")
        headless: 헤드리스 모드 (None이면 환경변수 사용)
        title: 공고명 (없으면 리포트 파일에서 조회)
        created_at: 수집일시 ISO 형식 (없으면 리포트 파일에서 조회)
    
    Returns:
        {
            "success": bool,
            "error": Optional[str],
            "attachments": List[Dict]
        }
    """
    # 공고 정보가 없으면 리포트 파일에서 조회
    if not title or not created_at:
        ann_info = get_announcement_info(announcement_number)
        if ann_info:
            title = title or ann_info.get('title')
            created_at = created_at or ann_info.get('created_at')
    
    url = build_detail_url(announcement_number, bid_ord)
    target_dir = ensure_download_dir(announcement_number, title=title, created_at=created_at)

    headless_env = os.getenv("PLAYWRIGHT_HEADLESS", "true").lower()
    headless_flag = headless if headless is not None else headless_env in ("true", "1", "yes")

    attachments: List[Dict] = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=headless_flag,
                args=[
                    "--disable-gpu",
                    "--disable-software-rasterizer",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                ],
            )
            context = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                accept_downloads=True,
            )
            page = context.new_page()
            page.goto(url, wait_until="networkidle", timeout=40000)
            page.wait_for_timeout(2000)

            # 첨부파일 그리드가 동적으로 생성되므로, 특정 테이블 여부와 무관하게 버튼/체크박스 기준으로 진행

            # 1) 전체 선택 체크박스 선택 (있으면)
            header_checkbox = page.locator(
                "#wq_uuid_1859_grdFile_CHK input[type=\"checkbox\"], #wq_uuid_1859_grdFile_CHK"
            )
            if header_checkbox.count():
                try:
                    header_checkbox.first.click(timeout=3000)
                    page.wait_for_timeout(300)
                except Exception:
                    pass

            # 2) 다운로드 버튼 클릭 (zip 형태로 묶여 내려오는 케이스)
            download_triggered = False
            for btn_id in [
                "wq_uuid_1859_btnFileDown",
                "wq_uuid_1859_btnDnld",
                "wq_uuid_1861_btnDnld",
                "wq_uuid_73_btnDnld",
                "mf_wfm_container_btnPdf",
            ]:
                btn = page.locator(f"#{btn_id}")
                if btn.count() == 0:
                    continue
                try:
                    with page.expect_download(timeout=20000) as dl_info:
                        btn.click()
                    download = dl_info.value
                    suggested = download.suggested_filename or f"{announcement_number}.zip"
                    save_path = target_dir / suggested
                    download.save_as(save_path)
                    file_size = save_path.stat().st_size if save_path.exists() else 0

                    attachment_entry = {
                        "name": suggested,
                        "suggested_filename": suggested,
                        "url": download.url,
                        "local_path": str(save_path),
                        "size": file_size,
                        "downloaded_at": datetime.now().isoformat(),
                    }

                    # zip이면 풀어서 하위 파일 목록 생성
                    if save_path.suffix.lower() == ".zip" and save_path.exists():
                        extracted_list: List[Dict] = []
                        try:
                            with zipfile.ZipFile(save_path, "r") as zf:
                                zf.extractall(target_dir)
                                for info in zf.infolist():
                                    extracted_path = target_dir / info.filename
                                    extracted_list.append(
                                        {
                                            "name": info.filename,
                                            "local_path": str(extracted_path),
                                            "size": info.file_size,
                                        }
                                    )
                            attachment_entry["extracted_files"] = extracted_list
                        except Exception as e:  # noqa: BLE001
                            attachment_entry["extract_error"] = f"압축 해제 실패: {str(e)}"

                    attachments.append(attachment_entry)
                    download_triggered = True
                    break
                except Exception as e:  # noqa: BLE001
                    attachments.append(
                        {
                            "name": f"download_from_{btn_id}",
                            "error": f"다운로드 실패: {str(e)}",
                        }
                    )

            browser.close()

            if not download_triggered:
                return {
                    "success": False,
                    "error": "다운로드가 트리거되지 않았습니다.",
                    "attachments": attachments,
                }

            return {
                "success": True,
                "attachments": attachments,
                "error": None,
            }
    except Exception as e:  # noqa: BLE001
        return {
            "success": False,
            "error": f"Playwright 처리 중 오류: {str(e)}",
            "attachments": attachments,
        }


def extract_text_from_file(file_path: Path) -> Tuple[str, str]:
    """
    첨부파일에서 텍스트 추출
    Returns:
        (status, text or error)
    """
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        try:
            import pypdf  # type: ignore

            reader = pypdf.PdfReader(str(file_path))
            texts = [page.extract_text() or "" for page in reader.pages]
            return "ok", "\n".join(texts)
        except Exception as e:  # noqa: BLE001
            return "error", f"PDF 추출 실패: {str(e)}"

    if suffix == ".docx":
        try:
            import docx  # type: ignore

            doc = docx.Document(str(file_path))
            texts = [p.text for p in doc.paragraphs]
            return "ok", "\n".join(texts)
        except Exception as e:  # noqa: BLE001
            return "error", f"DOCX 추출 실패: {str(e)}"

    if suffix == ".hwp":
        try:
            # hwp5 라이브러리를 사용한 텍스트 추출
            from hwp5.filestructure import Hwp5File
            from hwp5.recordstream import read_records
            from hwp5.binmodel import ParaText
            
            hwp5_file = Hwp5File(str(file_path))
            
            # BodyText에서 텍스트 추출
            texts = []
            
            if 'BodyText' in hwp5_file:
                bodytext = hwp5_file['BodyText']
                
                # 각 섹션 처리 (Section0, Section1, ...)
                for section_name in bodytext:
                    if section_name.startswith('Section'):
                        section = bodytext[section_name]
                        
                        # 레코드 스트림 읽기
                        try:
                            stream = section.open()
                            for record in read_records(stream):
                                # HWPTAG_PARA_TEXT 레코드에서 텍스트 추출
                                if record.get('tagname') == 'HWPTAG_PARA_TEXT':
                                    payload = record.get('payload')
                                    if payload:
                                        try:
                                            # ParaText 모델로 파싱
                                            para_text = ParaText(payload)
                                            # 텍스트 추출
                                            if hasattr(para_text, 'chars'):
                                                for char in para_text.chars:
                                                    if hasattr(char, 'ch'):
                                                        texts.append(char.ch)
                                                    elif isinstance(char, str):
                                                        texts.append(char)
                                        except Exception:
                                            # 파싱 실패 시 직접 디코딩 시도
                                            try:
                                                decoded = payload.decode('utf-16-le', errors='ignore')
                                                # 의미있는 텍스트만 추출
                                                cleaned = ''.join(
                                                    c for c in decoded 
                                                    if '\uAC00' <= c <= '\uD7A3' or  # 한글
                                                    '\u3131' <= c <= '\u318E' or  # 자모
                                                    c.isalnum() or c.isspace() or c in '.,;:!?()[]{}'
                                                )
                                                if cleaned.strip():
                                                    texts.append(cleaned)
                                            except Exception:
                                                pass
                        except Exception:
                            continue
            
            if texts:
                result_text = ''.join(texts).strip()
                if result_text:
                    return "ok", result_text
                else:
                    return "error", "HWP 파일에서 텍스트를 추출할 수 없습니다 (빈 문서일 수 있음)"
            else:
                return "error", "HWP 파일에서 텍스트를 찾을 수 없습니다"
                    
        except ImportError:
            return "error", "hwp5 라이브러리가 설치되지 않았습니다. pip install hwp5로 설치해주세요."
        except Exception as e:  # noqa: BLE001
            return "error", f"HWP 파일 처리 중 오류: {str(e)}"

    return "unsupported", f"{suffix} 포맷은 현재 추출을 지원하지 않습니다."


def summarize_attachment_text(text: str, max_chars: int = 1200) -> str:
    """
    텍스트 요약(간단 truncate) — 추후 ChatGPT 요약으로 교체 가능
    """
    text = text.strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "... (생략)"


def save_text_to_markdown(file_path: Path, text: str, output_dir: Optional[Path] = None) -> Path:
    """
    추출된 텍스트를 마크다운 파일로 저장
    
    Args:
        file_path: 원본 파일 경로
        text: 추출된 텍스트
        output_dir: 출력 디렉토리 (없으면 원본 파일과 같은 디렉토리)
    
    Returns:
        저장된 마크다운 파일 경로
    """
    if output_dir is None:
        output_dir = file_path.parent
    
    # 마크다운 파일명 생성 (원본 파일명에서 확장자만 .md로 변경)
    md_filename = file_path.stem + ".md"
    md_path = output_dir / md_filename
    
    # 마크다운 파일 작성
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(f"# {file_path.name}\n\n")
        f.write(f"**원본 파일**: `{file_path.name}`\n\n")
        f.write("---\n\n")
        f.write(text)
    
    return md_path


def analyze_attachments(
    announcement_number: str,
    bid_ord: str = "000",
    title: Optional[str] = None,
    created_at: Optional[str] = None,
) -> Dict:
    """
    첨부파일 다운로드 후 간단 텍스트 추출/요약 및 마크다운 파일 저장
    
    Args:
        announcement_number: 공고번호
        bid_ord: 입찰차수 (기본값: "000")
        title: 공고명 (없으면 리포트 파일에서 조회)
        created_at: 수집일시 ISO 형식 (없으면 리포트 파일에서 조회)
    """
    download_result = download_attachments(
        announcement_number,
        bid_ord=bid_ord,
        title=title,
        created_at=created_at,
    )
    if not download_result.get("success"):
        return download_result

    analyzed: List[Dict] = []
    for att in download_result.get("attachments", []):
        # 압축 파일 내 추출 목록 우선 처리
        extracted_files = att.get("extracted_files", [])
        if extracted_files:
            for ex in extracted_files:
                path = Path(ex["local_path"])
                status, text_or_err = extract_text_from_file(path)
                ex["extract_status"] = status
                if status == "ok":
                    ex["summary"] = summarize_attachment_text(text_or_err)
                    # 마크다운 파일로 저장
                    md_path = save_text_to_markdown(path, text_or_err)
                    ex["markdown_path"] = str(md_path)
                else:
                    ex["summary"] = text_or_err
            analyzed.append(att)
            continue

        if "local_path" not in att:
            att["summary"] = att.get("error", "파일이 다운로드되지 않았습니다.")
            analyzed.append(att)
            continue
        path = Path(att["local_path"])
        status, text_or_err = extract_text_from_file(path)
        att["extract_status"] = status
        if status == "ok":
            att["summary"] = summarize_attachment_text(text_or_err)
            # 마크다운 파일로 저장
            md_path = save_text_to_markdown(path, text_or_err)
            att["markdown_path"] = str(md_path)
        else:
            att["summary"] = text_or_err
        analyzed.append(att)

    return {
        "success": True,
        "attachments": analyzed,
        "error": None,
    }

