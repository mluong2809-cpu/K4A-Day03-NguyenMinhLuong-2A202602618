# 📊 BÁO CÁO THU HOẠCH NGHIỆM THU BÀI LAB 3 (BƯỚC 3 — SUBMISSION ARTIFACT)

> **Họ và Tên Học viên:** Nguyễn Minh Lương
> **Mã Sinh Viên / Mã Học viên:** 2A202602618
> **Chủ đề Lựa chọn:** Trợ lý Học vụ & Tra cứu lịch tư vấn VinUni

---

## 1. BẢNG CHẤM ĐIỂM AGENTIC FIT SCORING MATRIX (ĐÁNH GIÁ CHỦ ĐỀ)

| Tiêu chí Đánh giá           | Mức độ (1 - 5) | Giải trình chi tiết lý do chọn điểm                                                                                                                                                                                                |
| :-------------------------- | :------------: | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **1. Multi-step Reasoning** |   **4 / 5**    | Với yêu cầu tư vấn, Agent cần tách mục tiêu thành các bước: xác định mã sinh viên, tra cứu hồ sơ, đọc GPA/cố vấn và tổng hợp hoặc chuyển sang bước đặt lịch. Một câu hỏi giới thiệu quy chế đơn giản vẫn có thể trả lời trực tiếp. |
| **2. Tool Interaction**     |   **5 / 5**    | Dữ liệu học vụ và thao tác đặt lịch là dữ liệu/thao tác bên ngoài prompt. Agent phải gọi MCP tools `academic_query` và `schedule_appointment` để lấy dữ liệu chính xác và tạo booking.                                             |
| **3. Dynamic Decision**     |   **5 / 5**    | Sau khi nhận Observation từ `academic_query`, Agent phải quyết định tiếp theo theo kết quả: dùng đúng tên cố vấn để đặt lịch khi `SUCCESS`, hoặc dừng và thông báo rõ ràng khi `NOT_FOUND`; không được tự bịa dữ liệu.             |
| **4. Long Horizon Goal**    |   **3 / 5**    | Mục tiêu của mỗi phiên là hỗ trợ sinh viên hoàn tất tra cứu hoặc đặt lịch, có thể kéo dài qua vài lượt làm rõ thời gian/cố vấn. Tuy nhiên bài lab chưa cần lưu trạng thái dài hạn giữa nhiều phiên độc lập.                        |
| **TỔNG ĐIỂM AGENTIC FIT**   |  **17 / 20**   | _Điểm vượt 12/20: đề tài phù hợp để triển khai ReAct Agent với vòng lặp Thought → Action → Observation._                                                                                                                           |

---

## 2. TRÍCH XUẤT KẾT QUẢ WATERFALL TRACE LOG (SAU KHI CHẠY TEST SUITE TRÊN API THẬT)

> ⚠️ **YÊU CẦU NGHIỆM THU:** Mở tệp `.env` điền `GEMINI_API_KEY` (hoặc `OPENAI_API_KEY`) để kết nối LLM thật trước khi thực thi `python src/app.py --all`. Bài nộp chỉ dùng Mock Offline Provider sẽ không đạt điểm nghiệm thực tế.

Dán 1 đoạn trích xuất log tiêu biểu từ file `docs/trace_waterfall.json` sinh ra từ phản hồi LLM API thật:

> **Trạng thái chạy hiện tại:** Đã kết nối `GeminiProvider` với API key hợp lệ. TC01–TC03 chạy hoàn toàn trên Gemini thật; tại TC04, Gemini trả lỗi quota miễn phí `429 RESOURCE_EXHAUSTED` sau 5 request/phút nên các lượt còn lại fallback sang Mock. TC05 được Input Guardrail chặn cục bộ trước khi gọi LLM.

```json
[
  {
    "step": 1,
    "action_type": "TOOL_EXECUTION",
    "tool_name": "academic_query",
    "arguments": {
      "student_id": "SV2026002"
    },
    "observation": {
      "status": "SUCCESS",
      "student_id": "SV2026002",
      "data": {
        "full_name": "Trần Thị Bình",
        "advisor": "TS. Lê Thị B"
      }
    },
    "latency_ms": 0.01
  },
  {
    "step": 2,
    "action_type": "TOOL_EXECUTION",
    "tool_name": "schedule_appointment",
    "arguments": {
      "student_id": "SV2026002",
      "datetime_str": "09:30 16/09/2026",
      "advisor_name": "TS. Lê Thị B"
    },
    "observation": {
      "status": "SUCCESS",
      "booking_id": "BK-SV2026002-99",
      "message": "Đặt lịch thành công cho sinh viên SV2026002 với TS. Lê Thị B vào lúc 09:30 16/09/2026."
    },
    "latency_ms": 0.02
  }
]
```

---

## 3. TỔNG KẾT KẾT QUẢ NGHIỆM THU & NỘP BÀI

- [x] Đã điền API Key thật trong `.env` và xác nhận Agent kết nối thành công với Gemini API.
- **Tổng số Test Cases đã chạy thành công:** 5 / 5 test cases *(TC01–TC03 chạy Gemini thật; TC04 bị giới hạn quota và fallback một phần; TC05 bị Guardrail chặn cục bộ)*.
- **Số lượt gọi Tool qua MCP Server chính xác:** 4 lượt *(TC02: 1, TC03: 1, TC04: 2)*.
- **Input Guardrail:** TC05 đã bị chặn trước khi gửi tới LLM.
- **Interactive Chat CLI:** Đã smoke-test thành công thao tác khởi động và thoát bằng `exit`.
- **Kết quả đẩy Repo nộp bài:** [ ] Đã Commit và Push mã nguồn thành công lên GitHub cá nhân.

---

> ✅ **HOÀN TẤT NỘP BÀI:** Sao chép đường link GitHub Repository cá nhân của bạn và dán vào ô nộp bài trên hệ thống LMS VLearn để hoàn tất Bài Lab 3!
