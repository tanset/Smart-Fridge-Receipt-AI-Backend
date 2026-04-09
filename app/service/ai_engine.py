import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

class AIEngine:
    def __init__(self):
        api_key = os.getenv("API_KEY")
        if not api_key:
            raise ValueError("API_KEY environment variable is not set")

        # 新版 SDK 使用 Client 實例化
        self.client = genai.Client(api_key=api_key)
        self.model_id = "gemini-2.5-flash"

    async def parse_receipt(self, image_bytes: bytes, mime_type: str):
        """
        解析收據圖片並回傳結構化 JSON 數據
        """
        prompt = """
                  Analyze this receipt image and extract the food items.
                
                ### Instructions:
                1. **Noun-Only Extraction**: 
                   - Extract only the **core nouns** of the products.
                   - **Strictly remove all adjectives**, marketing terms, brands, and origins (e.g., remove "shady brook", "large", "mixed berry", "imported", "red", "easy peel", "herb", "3lb").
                   - Example: "shady brook large eggs" -> "eggs"
                   - Example: "imported red peppers" -> "peppers"
                   - Example: "21-25 easy peel shrimp 2lb" -> "shrimp"
                
                2. **Standardization**:
                   - Convert all names to lowercase.
                   - If multiple identical core nouns exist (e.g., different types of yogurt), keep them as separate entries or combine them if they are exactly the same noun.
                
                3. **Output Format**:
                   - Return ONLY a JSON object:
                   {
                     "items": [
                       {"name": "noun", "quantity": number}
                     ]
                   }
                
                Do not include markdown formatting or extra text.
                """

        try:
            # 使用新版 SDK 的 generate_content 方式
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=[
                    prompt,
                    types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
                ],
                config=types.GenerateContentConfig(
                    # 強制輸出格式為 JSON，這會自動移除 Markdown 標籤 (如 ```json)
                    response_mime_type="application/json"
                )
            )

            # 由於設定了 response_mime_type，response.text 直接就是 JSON 字串
            return json.loads(response.text)

        except Exception as e:
            return {
                "error": "AI Processing failed",
                "details": str(e)
            }

