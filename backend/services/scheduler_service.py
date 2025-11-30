from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from services.scraper_service import run_scraper
from services.filter_service import filter_announcements
from services.firebase_service import get_announcements
import os
from dotenv import load_dotenv

load_dotenv()

scheduler = BackgroundScheduler()

def scheduled_scrape():
    """스케줄된 시간에 공고 수집 실행"""
    keywords = os.getenv('SCRAPE_KEYWORDS', '').split(',')
    keywords = [k.strip() for k in keywords if k.strip()]
    
    print(f"스케줄된 공고 수집 시작 - 키워드: {keywords}")
    try:
        results = run_scraper(keywords=keywords)
        print(f"수집 완료: {len(results)}개 공고")
        
        # 수집된 공고 자동 필터링 및 검수
        if results:
            announcement_ids = [r.get('id') for r in results if r.get('id')]
            if announcement_ids:
                filter_results = filter_announcements(announcement_ids, keywords)
                print(f"필터링 완료: {len(filter_results)}개 공고 검수")
    except Exception as e:
        print(f"스케줄된 수집 중 오류: {str(e)}")

def start_scheduler():
    """스케줄러 시작"""
    # Cron 설정 (매일 오전 9시 실행)
    # 실제 사용 시 환경 변수나 설정 파일에서 읽어오도록 수정
    cron_hour = int(os.getenv('SCHEDULE_HOUR', 9))
    cron_minute = int(os.getenv('SCHEDULE_MINUTE', 0))
    
    scheduler.add_job(
        scheduled_scrape,
        trigger=CronTrigger(hour=cron_hour, minute=cron_minute),
        id='daily_scrape',
        name='일일 공고 수집',
        replace_existing=True
    )
    
    scheduler.start()
    print(f"스케줄러 시작됨 - 매일 {cron_hour:02d}:{cron_minute:02d}에 실행")

def stop_scheduler():
    """스케줄러 중지"""
    scheduler.shutdown()
    print("스케줄러 중지됨")

# 스케줄러 초기화 (앱 시작 시 자동 실행하려면 app.py에서 호출)
if __name__ == '__main__':
    start_scheduler()
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_scheduler()


