from pydantic import BaseModel, Field
from typing import Literal, List, Optional
from datetime import datetime

class UnifiedPost(BaseModel):
    post_id: str
    platform: Literal["youtube", "instagram", "facebook", "quora", "reddit", "twitter", "news"]
    author_id: str
    author_username: str
    text_content: str
    created_at: datetime
    metrics: dict = Field(default_factory=lambda: {"views": 0, "likes": 0, "shares": 0, "comments": 0})
    author_meta: dict = Field(default_factory=lambda: {"account_age_days": 0, "followers": 0, "verified": False})
    author_history: List[str] = Field(default_factory=list)
