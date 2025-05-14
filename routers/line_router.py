# routers/line_router.py
from fastapi import APIRouter, Request, HTTPException
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os

from datetime import datetime
from zoneinfo import ZoneInfo

# 全域定義台北時區
TZ_TPE = ZoneInfo("Asia/Taipei")

from services.llm_service        import classify_intent, classify_history, classify_pending, parse_reminder, chat_reply
from services.reminder_service   import add_reminder, list_history, list_pending
from services.db                 import SessionLocal

router = APIRouter()
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler      = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

@router.post("/callback")
async def callback(request: Request):
    signature = request.headers.get("X-Line-Signature","")
    body = await request.body()
    try:
        handler.handle(body.decode(), signature)
    except InvalidSignatureError:
        raise HTTPException(400, "Invalid signature")
    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    txt     = event.message.text

    # 1. 設提醒
    if classify_intent(txt):
        parsed = parse_reminder(txt)
        rec = add_reminder(user_id, parsed["event"], parsed["time"])
        # ───────── 以下是改動 ─────────

        dt = rec.time
        # 如果 rec.time 沒時區，就當作 UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo("UTC"))
        local = dt.astimezone(TZ_TPE)
        ts = local.strftime("%Y-%m-%d %H:%M:%S")
        reply = f"✅ 已設定提醒：{rec.event} 於 {ts}"
        # ────────────────────────────
    # 2. 查歷史
    elif classify_history(txt):
        db = SessionLocal()
        try:
            records = list_history(db, user_id)
            lines = []
            for r in records:
                local = r.time.astimezone(TZ_TPE)
                ts = local.strftime("%Y-%m-%d %H:%M:%S")
                lines.append(f"{ts} — {r.event} {'✅' if r.sent else '⏳'}")
            reply = "📜 這是你的提醒歷史：\n" + "\n".join(lines)   
        finally:
            db.close()

    # 3. 查 pending
    elif classify_pending(txt):
        db = SessionLocal()
        try:
            pendings = list_pending(db, user_id)
            if not pendings:
                reply = "👍 你目前沒有任何未觸發的提醒。"
            else:
                lines = [f"{r.time.isoformat()} — {r.event}" for r in pendings]
                reply = "⏳ 這是你尚未觸發的提醒：\n" + "\n".join(lines)
        finally:
            db.close()

    # 4. 其他聊天
    else:
        reply = chat_reply(user_id, txt)

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )