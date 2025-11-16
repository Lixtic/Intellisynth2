from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from app.database import SessionLocal
from app.models.log import LogEntry as LogModel

router = APIRouter()

class LogEntry(BaseModel):
    agent_id: str
    action_type: str
    input_data: dict
    output_data: dict
    timestamp: datetime

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/")
def receive_log(entry: LogEntry, db: Session = Depends(get_db)):
    log = LogModel(**entry.dict())
    db.add(log)
    db.commit()
    db.refresh(log)
    return {"status": "saved", "log_id": log.id}
