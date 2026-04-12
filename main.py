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
    return service.get_all_inventory(db)


@app.patch("/inventory", response_model=List[schemas.ItemResponse])
def update_inventory(
        updates: List[schemas.ItemUpdate],
        db: Session = Depends(get_db)
):
    # 呼叫新的批量更新 service
    updated_items = service.update_inventory_batch(db, updates)

    # 如果傳入列表但沒有任何一筆找到，可以視情況決定是否報錯
    # 這裡選擇直接回傳成功更新的清單（可能為空陣列）
    return updated_items

@app.delete("/inventory/bulk", status_code=200)
def bulk_delete_items(item_ids: List[int], db: Session = Depends(get_db)):
    deleted_count = service.bulk_soft_delete_inventory(db, item_ids)
    if deleted_count == 0:
        return {"message": "No valid items were found to delete"}
    return {"message": f"Successfully soft-deleted {deleted_count} items"}



@app.post("/inventory/recommend-menu")
async def recommend_menu(user_goal: str, db: Session = Depends(get_db)):
    # 1. 重用你既有的 service 函式獲取所有食材
    # 這裡得到的 items 是 SQLAlchemy 的 model 物件串列
    items = service.get_all_inventory(db)

    if not items:
        raise HTTPException(status_code=404, detail="Your fridge is empty. Cannot generate a menu.")

    # 2. 轉換格式：只提取 AI 需要的資訊 (名稱與數量)
    # 這樣可以減少傳送給 AI 的 Token 數量，省錢也比較快
    ingredients_list = [
        {
            "item_name": item.item_name,
            "current_quantity": item.current_quantity,
            "unit": item.unit
        }
        for item in items if item.current_quantity > 0
    ]

    # 3. 呼叫 ai_engine 裡面的 generate_menu 函式
    # 記得要用 await，因為 AI 請求是異步的
    result = await ai_engine.generate_menu(ingredients_list, user_goal)

    # 4. 檢查 AI 執行結果
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["details"])

    return result