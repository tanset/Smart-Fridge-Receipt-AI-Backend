import app.service.ai_engine as ai
from fastapi import UploadFile, HTTPException
engine = ai.AIEngine()
async def process_receipt_analysis(file: UploadFile):
    # 1. 檢查檔案格式
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File uploaded is not an image.")

    try:
        # 2. 讀取內容
        image_data = await file.read()
        current_mime = file.content_type

        # 3. 呼叫 AI 引擎
        # 建議在 service 層處理 AI 引擎的具體呼叫
        result = await engine.parse_receipt(image_data, mime_type=current_mime)

        return {
            "filename": file.filename,
            "mime_type": current_mime,
            "data": result
        }

    except Exception as e:
        # 在 service 層捕捉錯誤並拋出，或者根據業務需求處理
        raise Exception(f"AI Engine processing failed: {str(e)}")
    finally:
        await file.close()