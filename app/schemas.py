from pydantic import BaseModel
from typing import Optional

# 用於回傳資料給前端
class ItemResponse(BaseModel):
    id: int
    item_name: str
    unit: str
    current_quantity: float

    class Config:
        from_attributes = True

# 用於更新資料
class ItemUpdate(BaseModel):
    item_name: Optional[str] = None
    unit: Optional[str] = None
    current_quantity: Optional[float] = None