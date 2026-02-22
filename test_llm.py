"""测试LLM工具"""
import asyncio
import sys
sys.path.insert(0, 'D:/ai_dir/chip_fault_agent')

from src.mcp.server import get_mcp_server
from src.config.settings import get_settings

async def test_llm():
    print("=== 测试LLM工具 ===")
    if get_settings().ANTHROPIC_API_KEY:
        print(f"ANTHROPIC_API_KEY: {get_settings().ANTHROPIC_API_KEY[:20]}...")
    else:
        print("ANTHROPIC_API_KEY: 未配置")
    print(f"ANTHROPIC_BASE_URL: {get_settings().ANTHROPIC_BASE_URL}")
    print(f"ANTHROPIC_MODEL: {get_settings().ANTHROPIC_MODEL}")
    print()

    if not get_settings().ANTHROPIC_API_KEY:
        print("[X] 未配置LLM API密钥")
        return

    print("[OK] API密钥已配置")
    print()

    try:
        mcp_server = get_mcp_server()
        print("[OK] MCP服务器初始化成功")
        print()

        messages = [
            {"role": "system", "content": "你是一个芯片失效分析专家"},
            {"role": "user", "content": "请简单介绍一下CPU运算错误的常见原因（不超过100字）"}
        ]

        print("[SEND] 发送LLM请��...")
        result = await mcp_server.call_tool("llm_chat", {
            "messages": messages,
            "model": "glm-4.7",
            "temperature": 0.7,
            "max_tokens": 500
        })

        import json
        parsed_result = json.loads(result[0].text)
        print()
        print("[RECV] LLM响应:")
        print(json.dumps(parsed_result, ensure_ascii=False, indent=2))

        if parsed_result.get("success"):
            print()
            print("[SUCCESS] LLM调用成功!")
            content = parsed_result.get('content', '')
            print(f"[CONTENT] {content[:200]}...")
        else:
            print()
            print(f"[FAIL] LLM调用失败: {parsed_result.get('error')}")

    except Exception as e:
        print(f"[ERROR] 异常: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_llm())
