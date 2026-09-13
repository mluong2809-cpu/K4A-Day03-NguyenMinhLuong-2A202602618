"""
🛠️ TOOL DEFINITIONS & EXECUTION BACKEND
Mã nguồn chứa danh sách Tool Schemas (JSON Schema) và Execution Layer phục vụ cho MCP Server.
"""

import json
from typing import Dict, Any

# ==============================================================================
# 1. KHAI BÁO TOOL SCHEMAS CHUẨN NATIVE JSON SCHEMA (TASK 1.2)
# ==============================================================================

TOOLS_SCHEMA = [
    # Tool 1: Đã được định nghĩa mẫu sẵn cho Học viên tham khảo
    {
        "name": "academic_query",
        "description": "Tra cứu hồ sơ và thông tin học vụ của sinh viên VinUni bằng mã sinh viên.",
        "parameters": {
            "type": "object",
            "properties": {
                "student_id": {
                    "type": "string",
                    "description": "Mã sinh viên cần tra cứu (ví dụ: 'SV2026001')"
                }
            },
            "required": ["student_id"]
        }
    },
    
    {
        "name": "schedule_appointment",
        "description": "Đặt lịch hẹn tư vấn học vụ với Cố vấn học tập VinUni.",
        "parameters": {
            "type": "object",
            "properties": {
                "student_id": {
                    "type": "string",
                    "description": "Mã sinh viên cần đặt lịch (ví dụ: 'SV2026001')."
                },
                "datetime_str": {
                    "type": "string",
                    "description": "Thời gian hẹn theo định dạng HH:MM DD/MM/YYYY (ví dụ: '14:00 15/09/2026')."
                },
                "advisor_name": {
                    "type": "string",
                    "description": "Họ và tên cố vấn học tập sẽ tham gia buổi tư vấn."
                }
            },
            "required": ["student_id", "datetime_str", "advisor_name"]
        }
    },
    {
        "name": "update_student_profile",
        "description": "Cập nhật một trường thông tin trong hồ sơ sinh viên VinUni.",
        "parameters": {
            "type": "object",
            "properties": {
                "student_id": {
                    "type": "string",
                    "description": "Mã sinh viên có hồ sơ cần cập nhật (ví dụ: 'SV2026001')."
                },
                "field_to_update": {
                    "type": "string",
                    "description": "Tên trường hồ sơ cần cập nhật (ví dụ: 'email' hoặc 'phone_number')."
                },
                "new_value": {
                    "type": "string",
                    "description": "Giá trị mới hợp lệ cho trường hồ sơ được chọn."
                }
            },
            "required": ["student_id", "field_to_update", "new_value"]
        }
    }
]

# ==============================================================================
# 2. MÔ PHỎNG DỮ LIỆU & HÀM THỰC THI TOOL (EXECUTION LAYER)
# ==============================================================================

MOCK_DATABASE = {
    "SV2026001": {
        "full_name": "Nguyễn Văn An",
        "class": "AI-K4",
        "gpa": 3.85,
        "email": "an.nv@vinuni.edu.vn",
        "status": "Đang học",
        "advisor": "PGS.TS Nguyễn Văn A"
    },
    "SV2026002": {
        "full_name": "Trần Thị Bình",
        "class": "AI-K4",
        "gpa": 3.60,
        "email": "binh.tt@vinuni.edu.vn",
        "status": "Đang học",
        "advisor": "TS. Lê Thị B"
    }
}


def execute_academic_query(student_id: str) -> str:
    """Thực thi tra cứu học vụ theo mã sinh viên"""
    student = MOCK_DATABASE.get(student_id.strip().upper())
    if student:
        return json.dumps({
            "status": "SUCCESS",
            "student_id": student_id,
            "data": student
        }, ensure_ascii=False)
    else:
        return json.dumps({
            "status": "NOT_FOUND",
            "message": f"Không tìm thấy dữ liệu sinh viên có mã '{student_id}'"
        }, ensure_ascii=False)


def execute_schedule_appointment(student_id: str, datetime_str: str, advisor_name: str = "PGS.TS Nguyễn Văn A") -> str:
    """Thực thi đặt lịch hẹn tư vấn học vụ"""
    return json.dumps({
        "status": "SUCCESS",
        "booking_id": f"BK-{student_id}-99",
        "student_id": student_id,
        "datetime": datetime_str,
        "advisor": advisor_name,
        "message": f"Đặt lịch thành công cho sinh viên {student_id} với {advisor_name} vào lúc {datetime_str}."
    }, ensure_ascii=False)


def execute_update_student_profile(student_id: str, field_to_update: str, new_value: str) -> str:
    """Cập nhật thông tin liên hệ được phép trong hồ sơ sinh viên mock."""
    normalized_student_id = student_id.strip().upper()
    normalized_field = field_to_update.strip().lower()
    cleaned_value = new_value.strip()
    student = MOCK_DATABASE.get(normalized_student_id)

    if not student:
        return json.dumps({
            "status": "NOT_FOUND",
            "message": f"Không tìm thấy dữ liệu sinh viên có mã '{student_id}'"
        }, ensure_ascii=False)

    # Không cho tool nhạy cảm sửa điểm, lớp, trạng thái hoặc cố vấn học tập.
    allowed_fields = {"email", "phone_number"}
    if normalized_field not in allowed_fields:
        return json.dumps({
            "status": "INVALID_FIELD",
            "message": "Chỉ được cập nhật email hoặc phone_number qua công cụ này."
        }, ensure_ascii=False)

    if not cleaned_value:
        return json.dumps({
            "status": "INVALID_VALUE",
            "message": "Giá trị cập nhật không được để trống."
        }, ensure_ascii=False)

    old_value = student.get(normalized_field, "")
    student[normalized_field] = cleaned_value
    return json.dumps({
        "status": "SUCCESS",
        "student_id": normalized_student_id,
        "field_updated": normalized_field,
        "old_value": old_value,
        "new_value": cleaned_value,
        "message": f"Đã cập nhật {normalized_field} cho sinh viên {normalized_student_id}."
    }, ensure_ascii=False)


# Router gọi tool thực tế
TOOL_ROUTER = {
    "academic_query": execute_academic_query,
    "schedule_appointment": execute_schedule_appointment,
    "update_student_profile": execute_update_student_profile
}

def dispatch_tool_call(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Hàm trung chuyển thực thi tool"""
    if tool_name in TOOL_ROUTER:
        try:
            return TOOL_ROUTER[tool_name](**arguments)
        except Exception as e:
            return json.dumps({"status": "EXECUTION_ERROR", "error": str(e)}, ensure_ascii=False)
    return json.dumps({"status": "UNKNOWN_TOOL", "error": f"Tool '{tool_name}' không tồn tại!"}, ensure_ascii=False)
