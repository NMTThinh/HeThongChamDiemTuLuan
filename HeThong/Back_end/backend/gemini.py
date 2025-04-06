import os
import fitz
import asyncio
from dotenv import load_dotenv
import google.generativeai as genai
from database.database import gradingCriterias_collection
import json
from bson import ObjectId
import re

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("API Key không được tìm thấy. Hãy thiết lập biến môi trường GEMINI_API_KEY.")

genai.configure(api_key=API_KEY)

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = "\n".join(page.get_text("text") for page in doc)
    return text.strip()

def get_grading_criteria(selected_criteria_ids=None):
    if selected_criteria_ids:
        criteria_list = list(gradingCriterias_collection.find({"_id": {"$in": [ObjectId(id) for id in selected_criteria_ids]}}))
    else:
        criteria_list = list(gradingCriterias_collection.find({}))

    if not criteria_list:
        return "Không có tiêu chí chấm điểm cụ thể, chấm điểm theo cảm nhận tổng thể."

    formatted_criteria = "\n".join(
        f"- {criteria['name']}: {criteria.get('description', 'Không có mô tả')} (Tối đa {criteria['maxScore']} điểm)"
        for criteria in criteria_list
    )

    return f"Chấm theo các tiêu chí sau:\n{formatted_criteria}"

async def grade_essay_from_pdf(pdf_path, essay_title, selected_criteria_ids=None, temp=0.7):
    essay_text = extract_text_from_pdf(pdf_path)
    if not essay_text:
        return {"phù_hợp": "Không thể xác định", "điểm": "Không thể chấm điểm", "giải_thích": f"Không thể trích xuất nội dung từ {pdf_path}."}

    grading_criteria_text = get_grading_criteria(selected_criteria_ids)

    prompt = f"""
    Bạn là một giáo viên có thể chấm điểm nhiều môn học. Hãy chấm điểm bài tự luận sau theo thang điểm 10.

    Đề bài: {essay_title}

    {grading_criteria_text}

    Bài luận:
    {essay_text}

    Hãy đánh giá xem nội dung bài luận có phù hợp với đề bài hay không.

    Xuất kết quả theo định dạng JSON:
    {{
    "phù_hợp": "[Có/Không]",
    "điểm": "[Số điểm]",
    "giải_thích": "[Giải thích chi tiết]"
    }}
    """

    model = genai.GenerativeModel("gemini-1.5-pro")
    try:
        response = await model.generate_content_async(prompt, generation_config={"temperature": temp})
        print("Response from Gemini:", response.text)

        json_match = re.search(r'```json\s*(\{.*\})\s*```', response.text, re.DOTALL)
        json_text = json_match.group(1) if json_match else response.text

        result = json.loads(json_text)
        return result
    except json.JSONDecodeError:
        return {"phù_hợp": "Không thể xác định", "điểm": "Không thể chấm điểm", "giải_thích": response.text}
    except Exception as e:
        return {"phù_hợp": "Không thể xác định", "điểm": "Không thể chấm điểm", "giải_thích": f"Lỗi khi gọi Gemini API: {e}"}