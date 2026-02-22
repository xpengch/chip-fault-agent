"""直接测试LLMTool"""
import asyncio
import sys
sys.path.insert(0, 'D:/ai_dir/chip_fault_agent')

from src.mcp.tools.llm_tool import LLMTool
from src.config.settings import get_settings

async def test_llm():
    print("=== 直接测试LLMTool ===")
    settings = get_settings()

    print(f"ANTHROPIC_API_KEY: {settings.ANTHROPIC_API_KEY[:20] if settings.ANTHROPIC_API_KEY else 'None'}")
    print(f"ANTHROPIC_BASE_URL: {settings.ANTHROPIC_BASE_URL}")
    print()

    if not settings.ANTHROPIC_API_KEY:
        print("未配置LLM API密钥")
        return

    try:
        llm_tool = LLMTool()
        print("LLMTool initialized")
        print()

        messages = [
            {"role": "system", "content": "你是一个芯片失效分析��家"},
            {"role": "user", "content": "请用一句话介绍CPU运算错误"}
        ]

        print("Calling LLM...")
        result = await llm_tool.chat(messages, model="glm-4.7", temperature=0.7, max_tokens=500)

        print()
        print("Result:")
        for key, value in result.items():
            if key == "content":
                print(f"{key}: {value[:100]}...")
            else:
                print(f"{key}: {value}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_llm())
