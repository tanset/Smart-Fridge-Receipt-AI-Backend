from sqlalchemy.orm import Session
from app import models, schemas
from typing import List



def get_user_inventory(db: Session, user_id: int):
    return db.query(models.InventoryItem).filter(
        models.InventoryItem.user_id == user_id,
        models.InventoryItem.is_deleted == False
    ).all()


def update_inventory_batch(db: Session, updates: List[schemas.ItemUpdate], user_id: int):
    updated_items = []
    for data in updates:
        db_item = db.query(models.InventoryItem).filter(
            models.InventoryItem.id == data.id,
            models.InventoryItem.user_id == user_id
        ).first()

        if db_item:
            update_dict = data.model_dump(exclude_unset=True, exclude_none=True)
            for key, value in update_dict.items():
                if key != "id" and hasattr(db_item, key):
                    setattr(db_item, key, value)
            updated_items.append(db_item)
    db.commit()
    return updated_items


def bulk_update_or_create_inventory(db: Session, items: List[schemas.ItemCreate], user_id: int):
    for item in items:
        existing_item = db.query(models.InventoryItem).filter(
            models.InventoryItem.item_name == item.item_name,
            models.InventoryItem.unit == item.unit,
            models.InventoryItem.user_id == user_id,
            models.InventoryItem.is_deleted == False
        ).first()

        if existing_item:
            existing_item.current_quantity += item.current_quantity
        else:
            db_item = models.InventoryItem(
                item_name=item.item_name,
                unit=item.unit,
                current_quantity=item.current_quantity,
                user_id=user_id
            )
            db.add(db_item)
    db.commit()
    return {"message": "Inventory updated successfully"}


def bulk_soft_delete_inventory(db: Session, item_ids: List[int], user_id: int):
    query = db.query(models.InventoryItem).filter(
        models.InventoryItem.id.in_(item_ids),
        models.InventoryItem.user_id == user_id,
        models.InventoryItem.is_deleted == False
    )
    affected_rows = query.update({"is_deleted": True}, synchronize_session=False)
    db.commit()
    return affected_rows