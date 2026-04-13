from pydantic import BaseModel
from typing import Optional



class UserBase(BaseModel):
    username: str


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None

class ItemCreate(BaseModel):
    item_name: str
    unit: str
    current_quantity: float



class ItemUpdate(BaseModel):
    id: int
    item_name: Optional[str] = None
    unit: Optional[str] = None
    current_quantity: Optional[float] = None


class ItemResponse(BaseModel):
    id: int
    item_name: str
    unit: str
    current_quantity: float
    user_id: int

    class Config:
        from_attributes = True