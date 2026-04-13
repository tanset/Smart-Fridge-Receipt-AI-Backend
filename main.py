from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, status
from typing import List
from sqlalchemy.orm import Session
from app import database as db
from app import models, schemas
from app.service import inventory_service as service
from app.service import receipt_service
from app.service.ai_engine import ai_engine
from app.service import auth_service
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Define allowed origins for CORS
origins = [
    "http://localhost:3000",    # Default React port
    "http://127.0.0.1:3000",
    "https://your-frontend-domain.com", # Future production domain
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # Allow specific origins
    allow_credentials=True,      # Allow cookies or authentication info (e.g., JWT)
    allow_methods=["*"],         # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],         # Allow all headers
)

# Initialize database tables
models.Base.metadata.create_all(bind=db.engine)


# Dependency to get the database session
def get_db():
    database = db.SessionLocal()
    try:
        yield database
    finally:
        database.close()


# ==========================================
# 1. Authentication APIs
# ==========================================

@app.post("/auth/register", response_model=schemas.UserResponse)
def register(user: schemas.UserCreate, session: Session = Depends(get_db)):
    db_user = session.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    hashed_pwd = auth_service.get_password_hash(user.password)
    new_user = models.User(username=user.username, hashed_password=hashed_pwd)
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return new_user


@app.post("/auth/login", response_model=schemas.Token)
def login(user: schemas.UserCreate, session: Session = Depends(get_db)):
    db_user = session.query(models.User).filter(models.User.username == user.username).first()
    if not db_user or not auth_service.verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")

    # Store user_id in the 'sub' field of the Token
    access_token = auth_service.create_access_token(data={"sub": str(db_user.id)})
    return {"access_token": access_token, "token_type": "bearer"}


# ==========================================
# 2. Business APIs (JWT Protected)
# ==========================================

@app.post("/receipts/analyses")
async def analyze_receipt(
        file: UploadFile = File(...),
        current_user_id: int = Depends(auth_service.get_current_user)  # Token validation
):
    try:
        # Pass current_user_id to the service if needed to track who performed the analysis
        result = await receipt_service.process_receipt_analysis(file)
        return result
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/inventories")
async def save_corrected_items(
        items: List[schemas.ItemCreate],
        session: Session = Depends(get_db),
        current_user_id: int = Depends(auth_service.get_current_user)  # Token validation
):
    try:
        # Pass current_user_id to ensure data is saved under the correct user
        return service.bulk_update_or_create_inventory(session, items, current_user_id)
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/inventories", response_model=List[schemas.ItemResponse])
def read_inventory(
        session: Session = Depends(get_db),
        current_user_id: int = Depends(auth_service.get_current_user)
):
    # Fetch inventory belonging only to the current user
    return service.get_user_inventory(session, current_user_id)


@app.patch("/inventories", response_model=List[schemas.ItemResponse])
def update_inventory(
        updates: List[schemas.ItemUpdate],
        session: Session = Depends(get_db),
        current_user_id: int = Depends(auth_service.get_current_user)
):
    # Pass user_id to ensure users cannot update data belonging to others
    return service.update_inventory_batch(session, updates, current_user_id)


@app.delete("/inventories", status_code=200)
def bulk_delete_items(
        item_ids: List[int],
        session: Session = Depends(get_db),
        current_user_id: int = Depends(auth_service.get_current_user)
):
    # Pass user_id to ensure users can only delete their own data
    deleted_count = service.bulk_soft_delete_inventory(session, item_ids, current_user_id)
    if deleted_count == 0:
        return {"message": "No valid items were found to delete or permission denied"}
    return {"message": f"Successfully soft-deleted {deleted_count} items"}


@app.post("/inventories/recommendations")
async def recommend_menu(
        user_goal: str,
        session: Session = Depends(get_db),
        current_user_id: int = Depends(auth_service.get_current_user)
):
    # 1. Fetch all ingredients for the current user
    items = service.get_user_inventory(session, current_user_id)

    if not items:
        raise HTTPException(status_code=404, detail="Your fridge is empty.")

    ingredients_list = [
        {
            "item_name": item.item_name,
            "current_quantity": item.current_quantity,
            "unit": item.unit
        }
        for item in items if item.current_quantity > 0
    ]

    result = await ai_engine.generate_menu(ingredients_list, user_goal)

    if "error" in result:
        raise HTTPException(status_code=500, detail=result["details"])

    return result