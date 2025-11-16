from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

router = APIRouter()

class Rule(BaseModel):
    rule_id: str
    trigger: str
    conditions: List[str]
    severity: str

@router.post("/")
async def add_rule(rule: Rule):
    print(f"Rule added: {rule.rule_id}")
    return {"status": "rule added", "rule": rule}
