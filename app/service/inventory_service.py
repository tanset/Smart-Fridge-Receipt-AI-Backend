from sqlalchemy.orm import Session
from app import models, schemas
from typing import List


def get_all_inventory(db: Session):
    return db.query(models.InventoryItem).filter(models.InventoryItem.is_deleted == False).all()


def update_inventory_batch(db: Session, updates: List[schemas.ItemUpdate]):
    updated_items = []

    for data in updates:
        # 使用 .get() 是查詢主鍵 (Primary Key) 最快的方式
        db_item = db.query(models.InventoryItem).get(data.id)

        if db_item:
            # 轉換為字典，排除未設定與 null 的欄位
            update_dict = data.model_dump(exclude_unset=True, exclude_none=True)

            for key, value in update_dict.items():
                # 排除 id 欄位不更新，並確保 model 有該屬性
                if key != "id" and hasattr(db_item, key):
                    setattr(db_item, key, value)

            updated_items.append(db_item)

    try:
        db.commit()
        for item in updated_items:
            db.refresh(item)
        return updated_items
    except Exception as e:
        db.rollback()
        raise e


def bulk_update_or_create_inventory(db: Session, items: List[schemas.ItemCreate]):
    for item in items:
        # 檢查「名稱」與「單位」是否已存在
        existing_item = db.query(models.InventoryItem).filter(
            models.InventoryItem.item_name == item.item_name,
            models.InventoryItem.unit == item.unit
        ).first()

        if existing_item:
            # 若存在：直接累加庫存
            existing_item.current_quantity += item.quantity
        else:
            # 若不存在：建立新紀錄
            db_item = models.InventoryItem(
                item_name=item.item_name,
                unit=item.unit,
                current_quantity=item.current_quantity
            )
            db.add(db_item)

    db.commit()
    return {"message": "Inventory quantities updated successfully"}


def bulk_soft_delete_inventory(db: Session, item_ids: List[int]):
    # 找出所有在清單中且尚未被刪除的資料
    query = db.query(models.InventoryItem).filter(
        models.InventoryItem.id.in_(item_ids),
        models.InventoryItem.is_deleted == False
    )

    # 執行批量更新，將標記改為 True
    # synchronize_session=False 可以提高效能
    affected_rows = query.update({"is_deleted": True}, synchronize_session=False)

    db.commit()
    return affected_rows