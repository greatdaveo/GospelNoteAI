from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class SermonCreate(BaseModel):
    title: str
    summary: List[str]
    bible_references: List[str] = []

class SermonOutput(SermonCreate):
    id: int
    user_id: int
    created_at: datetime

class Config:
    orm_mode = True

class SermonUpdate(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    bible_references: Optional[List[str]]
