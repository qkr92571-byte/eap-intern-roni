"""
슬랙 메시지 전송 서비스
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from dotenv import load_dotenv

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
    if not channel_id:
        channel_id = os.getenv('SLACK_CHANNEL_ID')
    
    if not slack_token:
        print("❌ SLACK_BOT_TOKEN 환경변수가 설정되지 않았습니다.")
        return False
    
    if not channel_id:
        print("❌ SLACK_CHANNEL_ID 환경변수가 설정되지 않았습니다.")
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
            # 이미 전송된 경우 중복 방지
            if report_data.get('slack_sent', False):
                print(f"⚠️  이 리포트는 이미 슬랙으로 전송되었습니다.")
                print(f"   중복 전송을 방지하기 위해 건너뜁니다.")
                return True
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
        # 실제로 EAP와 관련이 있는 적합 공고만 카운트
        approved_count = sum(1 for a in announcements 
                           if a.get('status') == 'approved' 
                           and ('근로자지원프로그램' in a.get('title', '') 
                                or 'EAP' in a.get('title', '') 
                                or 'employee assistance program' in a.get('title', '').lower()))
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
        
        # 2. 유저 그룹 멘션 (EAP 파트)
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "<!subteam^S08SE5ZTPQD|@eap파트>"
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
        if approved_count > 0 or rejected_count > 0 or pending_count > 0:
            stats_text += f"\n  • 적합: {approved_count}개"
            stats_text += f"\n  • 부적합: {rejected_count}개"
            stats_text += f"\n  • 미검수: {pending_count}개"
        
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": stats_text
            }
        })
        
        # 5. 적합 공고 목록 (최대 5개)
        # 실제로 EAP와 관련이 있는 공고만 필터링 (제목에 "근로자지원프로그램" 또는 "EAP" 포함)
        all_approved = [a for a in announcements if a.get('status') == 'approved']
        approved_announcements = []
        for ann in all_approved:
            title = ann.get('title', '')
            # 실제로 EAP와 관련이 있는 공고만 포함
            if '근로자지원프로그램' in title or 'EAP' in title or 'employee assistance program' in title.lower():
                approved_announcements.append(ann)
        
        approved_announcements = approved_announcements[:5]  # 최대 5개
        
        if approved_announcements:
            approved_text = ":white_check_mark: *적합 공고 (최대 5개)*\n"
            for i, ann in enumerate(approved_announcements, 1):
                title = ann.get('title', '제목 없음')
                agency = ann.get('agency', '-')
                budget = ann.get('budget_amount', 0)
                budget_str = f"{budget:,}원" if budget else "-"
                approved_text += f"{i}. *{title}*\n   기관: {agency} | 예산: {budget_str}\n"
            
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": approved_text
                }
            })
        
        # 6. 전체 리포트 링크 (프론트엔드 URL)
        frontend_url = os.getenv('FRONTEND_URL', 'http://172.30.1.41:3000')
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*전체 리포트*\n<{frontend_url}|프론트엔드에서 보기>"
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
            text=f"EAP 공고 리포트 - {formatted_date}"
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

