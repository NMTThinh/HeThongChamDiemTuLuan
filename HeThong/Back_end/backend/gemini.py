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
        return {"phù_hợp": "Không thể xác định", "điểm_tổng": "Không thể chấm điểm", "giải_thích_chung": f"Không thể trích xuất nội dung từ {pdf_path}."}

    criteria_list_objects = []
    if selected_criteria_ids:
        criteria_list_objects = list(gradingCriterias_collection.find({"_id": {"$in": [ObjectId(id) for id in selected_criteria_ids]}}))
    else:
        criteria_list_objects = list(gradingCriterias_collection.find({}))

    grading_criteria_text = get_grading_criteria(selected_criteria_ids)

    # Tạo phần các tiêu chí động trong prompt và định dạng JSON mẫu
    criteria_placeholders = ""
    criteria_results = ""
    for criteria in criteria_list_objects:
        criteria_name_snake_case = re.sub(r'\s+', '_', criteria['name']).lower()
        criteria_placeholders += f'\n    - Mức độ {criteria["name"]} (nếu có trong tiêu chí).'
        criteria_results += f'\n    "{criteria_name_snake_case}": "[Số điểm]",'

    prompt = f"""
  Bạn là một giáo viên nhiều năm kinh nghiệm, có khả năng chấm điểm đa môn học. 
  Tuy nhiên, với mỗi bài tự luận, bạn phải tuyệt đối tuân thủ đặc thù và yêu cầu của môn học tương ứng.
    Hãy chấm điểm bài tự luận sau theo thang điểm 10, chỉ dựa trên các tiêu chí đã cung cấp của môn học.
      Đảm bảo đánh giá đúng trọng tâm, nội dung và tiêu chí của môn học này, không áp dụng tiêu chí của môn học khác.

    Đề bài: {essay_title}

    {grading_criteria_text}

    Bài luận:
    {essay_text}

    Hãy đánh giá xem:
    - Nội dung bài luận có phù hợp với đề bài hay không.
    {criteria_placeholders}

    Xuất kết quả theo định dạng JSON, bao gồm điểm số cho từng tiêu chí và điểm tổng (tính toán nếu có thể):
    {{
    "phù_hợp": "[Có/Không]",
    "giải_thích_chung": "[Giải thích rõ ràng, kỹ càng]",
    "giải_thích_chi_tiết": "[điểm đạt được của tiêu chí/điểm tối đa tiêu chí, Giải thích tại sao tiêu chí đó được điểm đó]",
    "điểm_tổng": "[Số điểm]",
    {criteria_results}
    }}
    """

    model = genai.GenerativeModel("gemini-2.0-flash")
    try:
        response = await model.generate_content_async(prompt, generation_config={"temperature": temp})
        print("Response from Gemini:", response.text)

        json_match = re.search(r'```json\s*(\{.*\})\s*```', response.text, re.DOTALL)
        json_text = json_match.group(1) if json_match else response.text

        result = json.loads(json_text)
        return result
    except json.JSONDecodeError:
        return {"phù_hợp": "Không thể xác định", "điểm_tổng": "Không thể chấm điểm", "giải_thích_chung": response.text}
    except Exception as e:
        return {"phù_hợp": "Không thể xác định", "điểm_tổng": "Không thể chấm điểm", "giải_thích_chung": f"Lỗi khi gọi Gemini API: {e}"}