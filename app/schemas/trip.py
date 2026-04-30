from datetime import datetime

from pydantic import BaseModel


class TripCreate(BaseModel):
    name: str


class MemberInfo(BaseModel):
    user_id: int
    email: str
    joined_at: datetime


class TripResponse(BaseModel):
    id: int
    name: str
    owner_id: int
    created_at: datetime
    members: list[MemberInfo] = []


class AddMemberRequest(BaseModel):
    email: str


class ContextItem(BaseModel):
    key: str
    value: str
    confidence: float
    updated_at: datetime


class TripContextResponse(BaseModel):
    trip_id: int
    items: list[ContextItem]
