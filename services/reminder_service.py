# services/reminder_service.py

from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.orm import Session
import uuid

from .db import Base, engine, SessionLocal
# ORM model
class ReminderModel(Base):
    __tablename__ = "reminders"
    id      = Column(String(36), primary_key=True, index=True)
    user_id = Column(String(64), index=True, nullable=False)
    event   = Column(String(256), nullable=False)
    time    = Column(DateTime, nullable=False)
    sent    = Column(Boolean, default=False, nullable=False)

# 建表（只需要執行一次）
Base.metadata.create_all(bind=engine)

def add_reminder(user_id: str, event: str, time_iso: str):
    from datetime import datetime
    db: Session = SessionLocal()
    remind_dt = datetime.fromisoformat(time_iso)
    rec = ReminderModel(
        id=str(uuid.uuid4()),
        user_id=user_id,
        event=event,
        time=remind_dt,
        sent=False
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    db.close()
    return rec

def list_reminders(db: Session):
    """回傳所有 reminders（包含 sent=True/False）"""
    return db.query(ReminderModel).all()

def list_today(db: Session, user_id: str):
    """回傳指定 user_id，今天的 reminders"""
    from datetime import datetime
    today = datetime.now().date()
    return (
        db.query(ReminderModel)
          .filter(
            ReminderModel.user_id == user_id,
            ReminderModel.time >= datetime.combine(today, datetime.min.time()),
            ReminderModel.time <= datetime.combine(today, datetime.max.time())
          )
          .all()
    )

def list_history(db: Session, user_id: str):
    """回傳指定 user_id 的所有提醒（不論 sent 狀態）"""
    return (
        db.query(ReminderModel)
          .filter(ReminderModel.user_id == user_id)
          .order_by(ReminderModel.time.asc())
          .all()
    )

def list_pending(db: Session, user_id: str):
    """
    回傳指定 user_id 尚未發送（sent=False）的提醒，
    依時間排序。
    """
    from datetime import datetime, time
    return (
        db.query(ReminderModel)
          .filter(
            ReminderModel.user_id == user_id,
            ReminderModel.sent == False
          )
          .order_by(ReminderModel.time.asc())
          .all()
    )