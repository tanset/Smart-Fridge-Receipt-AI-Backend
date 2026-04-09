from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from typing import Dict, List
from app.service.ai_engine import AIEngine
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.service import inventory_service as service
from app import database as db
from app import models, schemas
from app.service import receipt_service
app = FastAPI()
ai_engine = AIEngine()

@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}

@app.post("/analyze-receipt")
async def analyze_receipt(file: UploadFile = File(...)):
    try:
        # 直接委託給 Service 處理
        result = await receipt_service.process_receipt_analysis(file)
        return result
    except HTTPException as he:
        # 重新拋出已知的 HTTP 異常
        raise he
    except Exception as e:
        # 處理非預期的錯誤
        raise HTTPException(status_code=500, detail=str(e))



models.Base.metadata.create_all(bind=db.engine)
class ItemCreate(BaseModel):
    item_name: str
    unit: str
    quantity: float  # 前端傳入本次新增的數量

def get_db():
    database = db.SessionLocal()
    try:
        yield database
    finally:
        database.close()


@app.post("/inventory/save")
async def save_corrected_items(
    items: List[schemas.ItemCreate],
    db: Session = Depends(get_db)
):
    try:
        # 呼叫封裝好的服務邏輯
        return service.bulk_update_or_create_inventory(db, items)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/inventory", response_model=List[schemas.ItemResponse])
def read_inventory(db: Session = Depends(get_db)):
    return service.inventory_service.get_all_inventory(db)

@app.patch("/inventory/{item_id}", response_model=schemas.ItemResponse)
def update_inventory(item_id: int, update_data: schemas.ItemUpdate, db: Session = Depends(get_db)):
    updated_item = service.inventory_service.update_inventory_item(db, item_id, update_data)
    if not updated_item:
        raise HTTPException(status_code=404, detail="Item not found")
    return updated_item