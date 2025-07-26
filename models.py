from dataclasses import dataclass
from typing import Optional
from enum import Enum


class ParticipationStatus(Enum):
    ALWAYS = "always"
    NEVER = "never"
    ASK_EACH_TIME = "ask_each_time"


@dataclass
class User:
    user_id: int
    username: Optional[str]
    first_name: str
    last_name: Optional[str]
    bio: Optional[str]
    interests: Optional[str]
    participation_status: ParticipationStatus
    is_active: bool = True
    created_at: Optional[str] = None
