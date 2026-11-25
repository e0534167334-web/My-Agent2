from datetime import datetime
from enum import Enum
from uuid import uuid4
from pydantic import BaseModel, Field, field_validator
from config import TIMEZONE
class LocalTimeModel(BaseModel):
    @field_validator('start_at','end_at','remind_at',check_fields=False)
    @classmethod
    def normalize(cls,v):
        if v is None: return v
        return v.replace(tzinfo=TIMEZONE) if v.tzinfo is None else v.astimezone(TIMEZONE)
class EventType(str,Enum):
    EXAM='exam'; QUIZ='quiz'; PROJECT='project'; TASK='task'; MEETING='meeting'; OTHER='other'
class Priority(str,Enum):
    LOW='low'; MEDIUM='medium'; HIGH='high'
class Event(LocalTimeModel):
    id: str = Field(default_factory=lambda:str(uuid4()))
    title: str = Field(min_length=1,max_length=200)
    event_type: EventType
    start_at: datetime
    end_at: datetime|None=None
    priority: Priority=Priority.MEDIUM
    preparation_hours: float=Field(default=0,ge=0,le=200)
    reminder_enabled: bool=True
    description: str=Field(default='',max_length=2000)
class Reminder(LocalTimeModel):
    id: str=Field(default_factory=lambda:str(uuid4()))
    event_id: str
    remind_at: datetime
    message: str=Field(min_length=1,max_length=500)
class StudySession(LocalTimeModel):
    event_id: str
    start_at: datetime
    end_at: datetime
class AvailabilitySlot(LocalTimeModel):
    start_at: datetime
    end_at: datetime
class UserPreferences(BaseModel):
    available_slots: list[AvailabilitySlot]=Field(default_factory=list)
class StudyPlan(BaseModel):
    events: list[Event]=Field(default_factory=list)
    reminders: list[Reminder]=Field(default_factory=list)
    study_sessions: list[StudySession]=Field(default_factory=list)
class Extraction(BaseModel):
    events: list[Event]=Field(default_factory=list)
    questions: list[str]=Field(default_factory=list)
class Sessions(BaseModel):
    study_sessions: list[StudySession]=Field(default_factory=list)
