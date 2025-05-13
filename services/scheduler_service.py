# services/scheduler_service.py

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from linebot.models import TextSendMessage
from .db import SessionLocal
from .reminder_service import list_reminders, ReminderModel

def start_scheduler(line_bot_api):
    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: _job(line_bot_api), 'interval', seconds=30)
    scheduler.start()

def _job(line_bot_api):
    now_ts = datetime.now().astimezone().timestamp()
    db = SessionLocal()

    try:
        # 1. 先抓出所有 reminder
        reminders = list_reminders(db)

        for r in reminders:
            if r.sent:
                continue

            # 2. 直接拿 r.time （已是 datetime）
            remind_time = r.time

            # 3. 比較 timestamp
            if remind_time.timestamp() <= now_ts:
                # 4. 推播到 LINE
                line_bot_api.push_message(
                    r.user_id,
                    TextSendMessage(text=f"🔔 提醒你：{r.event} （{remind_time.isoformat()}）")
                )
                # 5. 標記已發送並寫回 DB
                r.sent = True
                db.add(r)

        db.commit()

    except Exception as e:
        print(f"⛔️ Scheduler error: {e}")
        db.rollback()
    finally:
        db.close()
