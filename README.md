# Smart Fridge & Receipt AI Backend

This is a FastAPI-based backend system designed to help users manage their food inventory. It leverages Google Gemini AI to analyze receipts and provide personalized meal recommendations based on current stock.

## 1. Project Architecture & File Functions

### Architecture Diagram
```text
+---------------------+        +------------------------------------------+
|  Client (Frontend)  | <----> |             FastAPI (main.py)            |
+---------------------+        +------------------------------------------+
                                    |                  |
                    +---------------+                  +-----------------+
                    |                                                    |
        [ Business Logic ]                                     [ Data & Config ]
        +----------------------------+                  +-------------------------+
        | - auth_service.py          |                  | - database.py (Session) |
        | - inventory_service.py     |                  | - models.py (SQLAlchemy)|
        | - receipt_service.py       |                  | - schemas.py (Pydantic) |
        | - ai_engine.py (Gemini AI) |                  | - .env (Secrets)        |
        +----------------------------+                  +-------------------------+
                    |
          +---------+---------+
          |                   |
    [ PostgreSQL ]      [ Google AI ]
```

### File Descriptions
- **`main.py`**: The application entry point. It initializes the FastAPI instance, configures CORS, handles database table creation, and defines all API routes.
- **`database.py`**: Configures the SQLAlchemy database engine and session factory using environment variables.
- **`models.py`**: Defines the SQLAlchemy ORM models (`User` and `InventoryItem`) representing the database schema.
- **`schemas.py`**: Contains Pydantic models for data validation, ensuring consistent input and output formats for the API.
- **`auth_service.py`**: Handles user authentication, including password hashing (Bcrypt) and JWT (JSON Web Token) generation/validation.
- **`inventory_service.py`**: Contains the core business logic for inventory CRUD operations (Create, Read, Update, Delete).
- **`receipt_service.py`**: Orchestrates the process of receiving an image file and passing it to the AI engine for analysis.
- **`ai_engine.py`**: Communicates with the Google Gemini API to perform receipt parsing and menu generation.

---

## 2. API Documentation

### Authentication APIs
| Method | Endpoint | Description | Input (JSON) | Output (JSON) |
| :--- | :--- | :--- | :--- | :--- |
| POST | `/auth/register` | Register a new user | `{username, password}` | `UserResponse` |
| POST | `/auth/login` | Login and get JWT | `{username, password}` | `Token` (JWT) |

### Business APIs (Requires Bearer Token)
| Method | Endpoint | Description | Input Format | Output Format |
| :--- | :--- | :--- | :--- | :--- |
| POST | `/receipts/analyses` | Analyze receipt image | `multipart/form-data` (file) | JSON object with item list |
| POST | `/inventories` | Save/Update items | `List[ItemCreate]` | Success message |
| GET | `/inventories` | Get user inventory | None | `List[ItemResponse]` |
| PATCH | `/inventories` | Batch update items | `List[ItemUpdate]` | `List[ItemResponse]` |
| DELETE| `/inventories` | Batch soft-delete | `List[int]` (IDs) | Success message |
| POST | `/inventories/recommendations` | Get AI menu | `user_goal` (Query Param) | JSON with meal details |

---

## 3. Environment Configuration (.env)

Create a `.env` file in the root directory and populate it with the following variables:

```env
API_KEY=your_google_gemini_api_key
DB_USER=your_db_username
DB_PASSWORD=your_db_password
DB_HOST=your_db_host
DB_PORT=5432
DB_NAME=your_database_name
SECRET_KEY=your_jwt_secret_key_for_signing
```

---

## 4. Database Setup

1. **Manual Creation**: Before running the application, you must manually create a PostgreSQL database. The name must match the `DB_NAME` value in your `.env` file.
2. **Automatic Table Initialization**: Once the application starts, `main.py` will execute `models.Base.metadata.create_all()`, which automatically creates the `users` and `inventory` tables if they do not exist.
3. **Resetting Data**: If you need to modify the schema (e.g., adding columns to `models.py`), you must first drop the existing tables in your database. The system will recreate them upon the next startup.

---

## 5. Frontend Integration (CORS)

The backend is configured to support specific frontend origins. In `main.py`, the `origins` list defines which domains are allowed to make cross-origin requests:

```python
origins = [
    "http://localhost:3000",      # Default React development port
    "[http://127.0.0.1:3000](http://127.0.0.1:3000)",      # Local IP address
    "[https://your-frontend-domain.com](https://your-frontend-domain.com)", # Production domain
]
```

To add a new environment (e.g., a mobile app or a staged site), simply append the URL to this list.
