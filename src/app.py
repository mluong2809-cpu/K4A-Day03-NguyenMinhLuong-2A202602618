"""
🚀 CORE AGENT APPLICATION (DAY 03: CHATBOT VS REACT AGENT)
Thực thi so sánh giữa Chatbot Baseline (Cấp 2) và ReAct Agent kết nối MCP Server (Cấp 3).
"""

import json
import os
import sys
import time
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from mcp_server import MCPAcademicServer
from prompts import (
    CHATBOT_BASELINE_PROMPT,
    REACT_AGENT_SYSTEM_PROMPT,
    MAX_ITERATIONS,
    check_input_prompt_injection
)
from providers import get_llm_provider

load_dotenv()

SENSITIVE_TOOLS = {"update_student_profile"}


def is_sensitive_tool(tool_name: str) -> bool:
    """Xác định tool thay đổi dữ liệu và bắt buộc phải có phê duyệt HITL."""
    return tool_name in SENSITIVE_TOOLS


def request_hitl_confirmation(tool_name: str, arguments: dict, interactive_hitl: bool) -> bool:
    """Yêu cầu con người phê duyệt trước khi cho phép thực thi tool nhạy cảm."""
    print(f"⚠️ [HITL WARNING]: Tool '{tool_name}' là hành động nhạy cảm!")
    print(f"   Tham số đề xuất: {json.dumps(arguments, ensure_ascii=False)}")

    if not interactive_hitl:
        print("🛑 [HITL SAFE MODE]: Không thực thi tool trong chế độ tự động; yêu cầu được gắn nhãn chờ phê duyệt.")
        return False

    confirmation = input("Bạn có xác nhận thực thi hành động này không? (Y/N): ").strip().casefold()
    return confirmation in {"y", "yes"}


def load_test_cases():
    """Tải danh sách 5 test cases từ config/test_cases.json hoặc config/test_cases.example.json"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")
    if not os.path.exists(config_path):
        example_path = os.path.join(base_dir, "config", "test_cases.example.json")
        if os.path.exists(example_path):
            print("⚠️ [CONFIG NOTICE]: Chưa thấy file 'config/test_cases.json'. Đang dùng mẫu 'config/test_cases.example.json'.")
            print("👉 Hãy chạy: copy config/test_cases.example.json config/test_cases.json và viết test cases theo đề tài của bạn!\n")
            config_path = example_path
        else:
            config_path = "test_cases.json"
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_waterfall_trace(trace_data: list):
    """Ghi vết log Waterfall Trace Log ra file docs/trace_waterfall.json"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    docs_dir = os.path.join(base_dir, "docs")
    os.makedirs(docs_dir, exist_ok=True)
    trace_path = os.path.join(docs_dir, "trace_waterfall.json")
    with open(trace_path, "w", encoding="utf-8") as f:
        json.dump(trace_data, f, ensure_ascii=False, indent=2)
    print(f"📊 [OBSERVABILITY]: Đã lưu {len(trace_data)} sự kiện Waterfall Trace tại '{trace_path}'!")


def run_baseline_chatbot(user_query: str, provider):
    """Chạy Chatbot gốc (Cấp 2) không có công cụ gọi Tool"""
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
    is_injection, warning = check_input_prompt_injection(user_query)
    if is_injection:
        print(f"🛡️ [INPUT GUARDRAIL]: {warning}")
        return
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(f"🤖 Chatbot phản hồi:\n{response}")


def run_react_agent(
    user_query: str,
    provider,
    mcp_server: MCPAcademicServer,
    interactive_hitl: bool = False
) -> list:
    """
    [REACT AGENT LOOP] Thực thi vòng lặp Thought -> Action -> Observation với MCP Server
    Trả về danh sách trace log của phiên thực thi.
    """
    print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")

    is_injection, warning = check_input_prompt_injection(user_query)
    if is_injection:
        print(f"🛡️ [INPUT GUARDRAIL]: {warning}")
        return [{
            "step": 0,
            "query": user_query,
            "action_type": "INPUT_GUARDRAIL_BLOCK",
            "llm_provider": "NOT_CALLED",
            "output": warning,
            "latency_ms": 0.0
        }]
    
    step = 0
    trace_logs = []
    tools_list = mcp_server.list_tools()
    conversation_context = user_query
    provider_name = provider.__class__.__name__
    
    while step < MAX_ITERATIONS:
        step += 1
        step_start_time = time.time()
        print(f"\n--- 🔄 Vòng lặp ReAct Loop (Step {step}/{MAX_ITERATIONS}) ---")
        
        # Gọi LLM với Native Tool Calling Specs
        llm_response = provider.generate_with_tools(
            conversation_context,
            tools_list,
            system_prompt=REACT_AGENT_SYSTEM_PROMPT
        )
        latency_ms = round((time.time() - step_start_time) * 1000, 2)
        
        thought = llm_response.get("thought", "Đang suy luận...")
        print(f"🧠 [Thought]: {thought}")
        
        # Trường hợp 1: LLM quyết định trả lời bằng văn bản trực tiếp
        if llm_response.get("type") == "text":
            final_content = llm_response.get("content", "")
            print(f"🏁 [Final Answer]: {final_content}")
            trace_logs.append({
                "step": step,
                "query": user_query,
                "action_type": "FINAL_ANSWER",
                "llm_provider": provider_name,
                "thought": thought,
                "output": final_content,
                "latency_ms": latency_ms
            })
            break
            
        # Trường hợp 2: LLM đề xuất gọi Tool (Action)
        elif llm_response.get("type") == "tool_call":
            tool_name = llm_response.get("tool_name")
            arguments = llm_response.get("arguments", {})
            
            print(f"🛠️ [Action Proposed]: {tool_name}({arguments})")

            if is_sensitive_tool(tool_name):
                approved = request_hitl_confirmation(tool_name, arguments, interactive_hitl)
                if not approved:
                    hitl_message = (
                        "Hành động nhạy cảm chưa được thực thi vì chưa có xác nhận của con người."
                    )
                    print(f"🏁 [Final Answer]: {hitl_message}")
                    trace_logs.append({
                        "step": step,
                        "query": user_query,
                        "action_type": "HITL_BLOCKED",
                        "llm_provider": provider_name,
                        "tool_name": tool_name,
                        "arguments": arguments,
                        "observation": {
                            "status": "PENDING_HUMAN_APPROVAL",
                            "message": hitl_message
                        },
                        "latency_ms": latency_ms
                    })
                    break

                print(f"✅ [HITL APPROVED]: Đã xác nhận thực thi tool '{tool_name}'.")
            
            # Thực thi Tool qua MCP Server
            mcp_result = mcp_server.call_tool(tool_name, arguments)
            obs_data = mcp_result.get("result", {})
            
            if not obs_data:
                print(f"👁️ [Observation từ MCP Server]: {{}}")
            else:
                obs_str = json.dumps(obs_data, ensure_ascii=False)
                print(f"👁️ [Observation từ MCP Server]: {obs_str}")
            
            trace_logs.append({
                "step": step,
                "query": user_query,
                "action_type": "TOOL_EXECUTION",
                "llm_provider": provider_name,
                "tool_name": tool_name,
                "arguments": arguments,
                "observation": obs_data,
                "latency_ms": latency_ms
            })
            
            # Nạp Observation vào ngữ cảnh để LLM suy luận ở lượt ReAct kế tiếp.
            conversation_context = (
                f"{user_query}\n\n[MCP_OBSERVATION]\n"
                f"{json.dumps(obs_data, ensure_ascii=False)}\n"
                "[/MCP_OBSERVATION]\n"
                "Hãy dùng Observation trên để tiếp tục suy luận và trả lời người dùng."
            )
        else:
            print("⚠️ [REACT WARNING]: LLM trả về kiểu phản hồi không hợp lệ.")
            break

    else:
        print(f"⚠️ [REACT WARNING]: Đã đạt giới hạn {MAX_ITERATIONS} vòng lặp.")

    return trace_logs


if __name__ == "__main__":
    print("==========================================================")
    print("🏫 VINUNI AI COURSE - DAY 03 LAB: CHATBOT VS REACT AGENT")
    print("==========================================================")
    
    provider = get_llm_provider()
    mcp_server = MCPAcademicServer()
    interactive_hitl = "--interactive-hitl" in sys.argv
    
    print(f"🔌 LLM Provider: {provider.__class__.__name__}")
    print(f"🌐 MCP Server: {mcp_server.server_name}\n")
    
    tests = load_test_cases()
    print(f"✅ Đã tải thành công {len(tests)} Test Cases thử nghiệm.\n")
    
    if "--interactive" in sys.argv:
        print("🎮 [INTERACTIVE MODE] Trò chuyện trực tiếp với ReAct Agent:")
        print("💡 Gợi ý câu hỏi thử nghiệm:")
        print("   - Câu hỏi chung: 'Quy chế học vụ VinUni yêu cầu bao nhiêu tín chỉ?'")
        print("   - Tra cứu học vụ: 'Hãy tra cứu thông tin học vụ của sinh viên SV2026001'")
        print("   - Đặt lịch hẹn: 'Đặt lịch hẹn tư vấn cho SV2026001 vào 14:00 ngày 15/09/2026'")
        print("   - Gõ 'exit' hoặc 'quit' để kết thúc phiên trò chuyện.\n")
        while True:
            try:
                user_input = input("👤 Sinh viên hỏi: ").strip()
                if not user_input or user_input.lower() in ["exit", "quit"]:
                    print("👋 Tạm biệt! Kết thúc phiên trò chuyện.")
                    break
                logs = run_react_agent(
                    user_input,
                    provider,
                    mcp_server,
                    interactive_hitl=interactive_hitl
                )
                save_waterfall_trace(logs)
            except (KeyboardInterrupt, EOFError):
                print("\n👋 Đã thoát phiên tương tác.")
                break
    elif "--all" in sys.argv:
        print("🚀 [TEST SUITE MODE] Kiểm tra 5 Test Cases:")
        completed_count = 0
        todo_count = 0
        all_traces = []
        
        for tc in tests:
            print(f"\n==================================================")
            print(f"🧪 [{tc['id']}] Loại test: {tc['type']} (Độ phức tạp: {tc['complexity']})")
            print(f"📌 Kỳ vọng: {tc['expected_behavior']}")
            
            if tc["question"].strip().startswith("TO" + "DO"):
                print(f"⏸️ [CHƯA KÍCH HOẠT - CÂU HỎI CHƯA HOÀN THIỆN]:")
                print(f"   {tc['question']}")
                print(f"   👉 Hãy mở file 'config/test_cases.json' để viết câu hỏi thực tế cho Test Case này!")
                todo_count += 1
            else:
                logs = run_react_agent(
                    tc["question"],
                    provider,
                    mcp_server,
                    interactive_hitl=interactive_hitl
                )
                all_traces.extend(logs)
                completed_count += 1
                
        print(f"\n==================================================")
        print(f"📊 [KẾT QUẢ TEST SUITE]: Đã thực thi {completed_count}/{len(tests)} Test Cases | {todo_count} Test Cases cần bổ sung câu hỏi")
        if all_traces:
            save_waterfall_trace(all_traces)
        print(f"💡 Để trò chuyện trực tiếp từng câu: Chạy 'python src/app.py --interactive'")
    else:
        # Chế độ mặc định khi chỉ gõ 'python src/app.py'
        print("ℹ️ HƯỚNG DẪN SỬ DỤNG CHƯƠNG TRÌNH:")
        print("  1. Chat trực tiếp liên tục:   python src/app.py --interactive")
        print("  2. Chạy toàn bộ Test Cases:    python src/app.py --all\n")
        
        sample_query = tests[1]["question"]
        print(f"--- 🏁 DEMO CHẠY THỬ 1 TEST CASE MẪU (TC02: Tra cứu học vụ) ---")
        logs = run_react_agent(
            sample_query,
            provider,
            mcp_server,
            interactive_hitl=interactive_hitl
        )
        save_waterfall_trace(logs)
        print("\n💡 Hãy thử ngay lệnh: python src/app.py --interactive để chat trực tiếp!")
