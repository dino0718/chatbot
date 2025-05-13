# routers/api_router.py
from fastapi import APIRouter, Request, Query
from sqlalchemy.orm import Session
from services.db import SessionLocal
from services.llm_service import classify_intent, parse_reminder, chat_reply
from services.reminder_service import add_reminder, list_today, list_history

api = APIRouter()

@api.post("/reminder")
async def set_or_chat(request: Request):
    data = await request.json()
    user_id = data.get("user_id", "")
    text    = data.get("message", "")

    # 1. 先判斷是否為提醒指令
    if classify_intent(text):
        # 2a. 是提醒：解析並存提醒
        parsed = parse_reminder(text)
        rec = add_reminder(user_id, parsed["event"], parsed["time"])
        return {
            "type": "reminder",
            "reminder": {
                "id":    rec.id,
                "event": rec.event,
                "time":  rec.time.isoformat()
            }
        }
    else:
        # 2b. 不是提醒：當一般聊天
        reply = chat_reply(user_id, text)
        return {
            "type": "chat",
            "reply": reply
        }


@api.get("/reminder/today")
def get_today_reminders(user_id: str = Query(...)):
    db: Session = SessionLocal()
    try:
        items = list_today(db, user_id)
        return {
            "today_reminders": [
                {"event": r.event, "time": r.time.isoformat()}
                for r in items
            ]
        }
    finally:
        db.close()


@api.get("/reminder/history")
def get_history(user_id: str = Query(...)):
    db: Session = SessionLocal()
    try:
        records = list_history(db, user_id)
        return {
            "history": [
                {
                    "id":    r.id,
                    "event": r.event,
                    "time":  r.time.isoformat(),
                    "sent":  r.sent
                }
                for r in records
            ]
        }
    finally:
        db.close()


@api.get("/debug")
def debug():
    db: Session = SessionLocal()
    try:
        all_reminders = db.query(type(list_history.__annotations__['return'])[0]).all()  # 直接查 model
        return {"reminders": [r.__dict__ for r in all_reminders]}
    finally:
        db.close()
