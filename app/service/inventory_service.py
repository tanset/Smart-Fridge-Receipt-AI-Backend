from sqlalchemy.orm import Session
from app import models, schemas
from typing import List


def get_all_inventory(db: Session):
    return db.query(models.InventoryItem).all()

def update_inventory_item(db: Session, item_id: int, update_data: schemas.ItemUpdate):
    db_item = db.query(models.InventoryItem).filter(models.InventoryItem.id == item_id).first()
    if db_item:
        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(db_item, key, value)
        db.commit()
        db.refresh(db_item)
    return db_item


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
                current_quantity=item.quantity
            )
            db.add(db_item)

    db.commit()
    return {"message": "Inventory quantities updated successfully"}