from app.service.ai_engine import ai_engine
from fastapi import UploadFile, HTTPException

async def process_receipt_analysis(file: UploadFile):
    # 1. Check file format
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File uploaded is not an image.")

    try:
        # 2. Read file content
        image_data = await file.read()
        current_mime = file.content_type

        # 3. Call the AI engine
        # It is recommended to handle specific AI engine calls within the service layer
        result = await ai_engine.parse_receipt(image_data, mime_type=current_mime)

        return {
            "filename": file.filename,
            "mime_type": current_mime,
            "data": result
        }

    except Exception as e:
        # Catch errors in the service layer and re-raise or handle based on business logic
        raise Exception(f"AI Engine processing failed: {str(e)}")
    finally:
        await file.close()