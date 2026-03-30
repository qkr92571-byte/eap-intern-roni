"""
슬랙 메시지 전송 서비스
"""

import os
import json
from datetime import datetime
from pathlib import Path
import re
from typing import List, Dict, Optional
from dotenv import load_dotenv
from utils.constants import SLACK_PRODUCTION_CHANNEL_ID

# 환경변수 로드
load_dotenv()

try:
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError
    import ssl
    import certifi
    HAS_SLACK_SDK = True
except ImportError:
    HAS_SLACK_SDK = False
    print("⚠️  slack_sdk가 설치되지 않았습니다.")
    print("   설치: pip install slack-sdk certifi")


def _build_g2b_detail_url(announcement_number: str) -> Optional[str]:
    """
    나라장터(차세대) 상세 페이지 URL 생성

    예)
    - announcement_number: R26BK01313635-000
    - URL: https://www.g2b.go.kr/link/PNPE027_01/single/?bidPbancNo=R26BK01313635&bidPbancOrd=000

    공고번호가 위 형태로 파싱되지 않으면 None 반환.
    """
    ann = (announcement_number or "").strip()
    if not ann:
        return None

    # 일반적으로 나라장터 공고번호는 "<bidPbancNo>-<bidPbancOrd>" 형태
    m = re.match(r"^(?P<no>[^-]+)-(?P<ord>\d+)$", ann)
    if not m:
        return None

    bid_no = m.group("no")
    bid_ord_raw = m.group("ord")
    # 나라장터 상세 URL은 보통 bidPbancOrd가 3자리(예: 000)인 경우가 많아 zero-padding 처리
    bid_ord = bid_ord_raw.zfill(3)
    return f"https://www.g2b.go.kr/link/PNPE027_01/single/?bidPbancNo={bid_no}&bidPbancOrd={bid_ord}"


def send_report_to_slack(
    report_file: str,
    slack_token: Optional[str] = None,
    channel_id: Optional[str] = None
) -> bool:
    """
    JSON 리포트를 슬랙으로 전송
    
    Args:
        report_file: 리포트 JSON 파일 경로
        slack_token: Slack Bot Token (없으면 환경변수에서 가져옴)
        channel_id: Slack Channel ID (없으면 환경변수에서 가져옴)
                    - 공식 전송: C034EQD6W4W (review_and_upload_report.py에서 사용)
                    - 개발 테스트: 환경변수 SLACK_CHANNEL_ID 사용
    
    Returns:
        전송 성공 여부
    """
    if not HAS_SLACK_SDK:
        print("❌ slack_sdk가 설치되지 않았습니다.")
        print("   설치: pip install slack-sdk certifi")
        return False
    
    # 환경변수에서 토큰과 채널 ID 가져오기
    if not slack_token:
        slack_token = os.getenv('SLACK_BOT_TOKEN')

    # 채널 ID 해석 (공식/테스트 분리 + 레거시 호환)
    # - SLACK_OFFICIAL_CHANNEL_ID: 공식 채널 (기본값: SLACK_PRODUCTION_CHANNEL_ID)
    # - SLACK_TEST_CHANNEL_ID: 테스트 채널
    # - SLACK_CHANNEL_ID: (레거시) 테스트 채널로 취급
    official_channel_id = os.getenv('SLACK_OFFICIAL_CHANNEL_ID', SLACK_PRODUCTION_CHANNEL_ID)
    test_channel_id = os.getenv('SLACK_TEST_CHANNEL_ID') or os.getenv('SLACK_CHANNEL_ID')

    if not channel_id:
        # 기존 동작(테스트 채널로 전송)을 유지하되, 새 변수 우선
        channel_id = test_channel_id
    
    if not slack_token:
        print("❌ SLACK_BOT_TOKEN 환경변수가 설정되지 않았습니다.")
        return False
    
    if not channel_id:
        print("❌ Slack 채널 ID가 설정되지 않았습니다.")
        print("   테스트 채널: SLACK_TEST_CHANNEL_ID (또는 레거시 SLACK_CHANNEL_ID)")
        print(f"   공식 채널(참고): SLACK_OFFICIAL_CHANNEL_ID (기본값 {official_channel_id})")
        return False
    
    try:
        # 리포트 파일 읽기
        report_path = Path(report_file)
        if not report_path.exists():
            print(f"❌ 리포트 파일을 찾을 수 없습니다: {report_file}")
            return False
        
        with open(report_path, 'r', encoding='utf-8') as f:
            report_data = json.load(f)
        
        # 리포트 데이터가 딕셔너리인 경우 (메타데이터 포함)
        if isinstance(report_data, dict):
            announcements = report_data.get('announcements', [])
            # 이미 전송된 경우 중복 방지 (채널별)
            if report_data.get('slack_sent', False):
                prev_channel = report_data.get('slack_channel')
                if prev_channel and prev_channel == channel_id:
                    print(f"⚠️  이 리포트는 이미 슬랙으로 전송되었습니다.")
                    print(f"   중복 전송을 방지하기 위해 건너뜁니다.")
                    return True
                # 다른 채널로는 전송 허용 (예: 테스트→공식)
                if prev_channel and prev_channel != channel_id:
                    print("⚠️  이 리포트는 다른 채널로 이미 전송된 이력이 있습니다.")
                    print(f"   이전 채널: {prev_channel}")
                    print(f"   이번 채널: {channel_id}")
        elif isinstance(report_data, list):
            announcements = report_data
        else:
            print("❌ 리포트 파일 형식이 올바르지 않습니다.")
            return False
        
        if not isinstance(announcements, list):
            print("❌ 리포트 파일 형식이 올바르지 않습니다.")
            return False
        
        # 리포트 정보 추출
        total_count = len(announcements)
        # 상태 기준 집계 (키워드 필터로 누락되던 문제 수정)
        approved_count = sum(1 for a in announcements if a.get('status') == 'approved')
        rejected_count = sum(1 for a in announcements if a.get('status') == 'rejected')
        pending_count = sum(1 for a in announcements if not a.get('reviewed', False))
        
        # 파일명에서 날짜 추출 (report_YYMMDD.json)
        date_str = report_path.stem.replace('report_', '')
        try:
            # YYMMDD -> YYYY-MM-DD 변환
            year = 2000 + int(date_str[:2])
            month = date_str[2:4]
            day = date_str[4:6]
            formatted_date = f"{year}-{month}-{day}"
        except:
            formatted_date = datetime.now().strftime('%Y-%m-%d')
        
        # 슬랙 메시지 구성
        blocks = []
        
        # 1. 헤더
        blocks.append({
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"📊 EAP 공고 리포트 - {formatted_date}",
                "emoji": True
            }
        })
        
        # 2. 유저 그룹 멘션 (EAP 파트) - 환경변수 우선
        usergroup_id = os.getenv('SLACK_EAP_USERGROUP', 'S08SE5ZTPQD')
        usergroup_mention = f"<!subteam^{usergroup_id}|@eap파트>"
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": usergroup_mention
            }
        })
        
        # 3. 검색일자
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f":date: *검색일자*\n{formatted_date}"
            }
        })
        
        # 4. 통계 정보
        stats_text = f":clipboard: *신규 공고*\n총 {total_count}개"
        stats_text += f"\n  • 적합: {approved_count}개"
        stats_text += f"\n  • 부적합: {rejected_count}개"
        
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": stats_text
            }
        })
        
        # 5. 적합 공고 목록 (전체 표시)
        all_approved = [a for a in announcements if a.get('status') == 'approved']
        
        if all_approved:
            # Slack mrkdwn 섹션 길이 제한(대략 3000자)을 피하기 위해, 여러 블록으로 나눠서 전송
            approved_lines = []
            for i, ann in enumerate(all_approved, 1):
                title = ann.get('title', '제목 없음')
                announcement_number = ann.get('announcement_number', '')
                
                # 적합 공고 리스트는 나라장터 상세 페이지로 바로 이동하도록 링크 생성
                # 예: https://www.g2b.go.kr/link/PNPE027_01/single/?bidPbancNo=R26BK01313635&bidPbancOrd=000
                g2b_link = _build_g2b_detail_url(announcement_number)

                # 링크가 있으면 공고명에 하이퍼링크 추가, 없으면 일반 텍스트
                if g2b_link:
                    title_with_link = f"<{g2b_link}|{title}>"
                else:
                    title_with_link = title

                approved_lines.append(f"{i}. *{title_with_link}*")

            # 블록 분할(너무 길면 Slack 전송 실패)
            max_section_chars = 2900
            header_text = ":white_check_mark: *적합 공고*\n"
            current = header_text

            def _flush(text: str) -> None:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": text.rstrip()
                    }
                })

            for line in approved_lines:
                addition = f"{line}\n"
                if len(current) + len(addition) > max_section_chars:
                    _flush(current)
                    # 이후 블록은 헤더를 짧게 유지
                    current = ":white_check_mark: *적합 공고 (계속)*\n" + addition
                else:
                    current += addition

                # Slack blocks는 최대 50개이므로, 과도한 분할로 실패하는 것을 방지
                # (마지막 전체 리포트 링크 블록을 위해 최소 1개는 남겨둠)
                if len(blocks) >= 49:
                    current += "\n⚠️ 적합 공고가 많아 일부만 표시됩니다."
                    break

            if current.strip():
                _flush(current)
        
        # 6. 전체 리포트 링크 (프론트엔드 URL)
        # 슬랙 메시지에서 "프론트엔드에서 보기" 링크가 랜딩될 기본 주소
        frontend_url = os.getenv('FRONTEND_URL', 'https://eap-intern-roni.web.app')
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*전체 리포트*\n<{frontend_url}|인턴로니 웹사이트 이동>"
            }
        })
        
        # 슬랙 메시지 전송
        print(f"📤 슬랙 메시지 전송 중...")
        print(f"   채널 ID: {channel_id}")
        print(f"   공고 수: {total_count}개")
        
        # SSL 컨텍스트 설정
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        
        # WebClient에 SSL 컨텍스트 전달
        client = WebClient(token=slack_token, ssl=ssl_context)
        
        response = client.chat_postMessage(
            channel=channel_id,
            blocks=blocks,
            text=f"{usergroup_mention} EAP 공고 리포트 - {formatted_date}"
        )
        
        # 리포트 파일에 전송 기록 저장 (중복 방지)
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                report_data = json.load(f)
            
            # 리포트 데이터가 리스트인 경우 딕셔너리로 변환
            if isinstance(report_data, list):
                report_data = {
                    'announcements': report_data,
                    'slack_sent': True,
                    'slack_sent_at': datetime.now().isoformat(),
                    'slack_channel': channel_id
                }
            else:
                # 전송 이력 누적 (선택적으로 관리)
                prev_channel = report_data.get('slack_channel')
                prev_sent_at = report_data.get('slack_sent_at')
                if prev_channel or prev_sent_at:
                    history = report_data.get('slack_sent_history')
                    if not isinstance(history, list):
                        history = []
                    # 마지막 전송 정보를 history에 보관
                    history.append({
                        'channel': prev_channel,
                        'sent_at': prev_sent_at,
                    })
                    report_data['slack_sent_history'] = history

                report_data['slack_sent'] = True
                report_data['slack_sent_at'] = datetime.now().isoformat()
                report_data['slack_channel'] = channel_id
            
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️  전송 기록 저장 실패 (무시): {str(e)}")
        
        print(f"✅ 슬랙 메시지 전송 완료!")
        print(f"   메시지 타임스탬프: {response['ts']}")
        return True
        
    except SlackApiError as e:
        print(f"❌ 슬랙 API 오류: {e.response['error']}")
        return False
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False


def send_daily_report_to_slack(date: Optional[datetime] = None) -> bool:
    """
    오늘 수집된 리포트를 슬랙으로 전송
    
    Args:
        date: 날짜 (기본값: 오늘)
    
    Returns:
        전송 성공 여부
    """
    from services.file_service import REPORT_DIR, get_date_string
    
    if date is None:
        date = datetime.now()
    
    date_str = get_date_string(date)
    report_file = REPORT_DIR / f'report_{date_str}.json'
    
    if not report_file.exists():
        print(f"❌ 리포트 파일을 찾을 수 없습니다: {report_file}")
        return False
    
    return send_report_to_slack(str(report_file))

