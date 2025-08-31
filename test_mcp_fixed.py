#!/usr/bin/env python3
"""
测试修复版本的MCP服务器
"""

import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_mcp_server():
    """测试MCP服务器连接和工具调用"""
    server_params = StdioServerParameters(
        command="python",
        args=["E:\\wd_mcp\\mcp_server_fixed.py"]
    )
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                print("🔗 正在连接MCP服务器...")
                await session.initialize()
                print("✅ MCP服务器连接成功!")
                
                # 列出可用工具
                print("\n📋 列出可用工具:")
                tools_result = await session.list_tools()
                print(f"找到 {len(tools_result.tools)} 个工具:")
                for tool in tools_result.tools:
                    print(f"  - {tool.name}: {tool.description}")
                
                # 测试 list_supported_formats 工具
                print("\n🔧 测试 list_supported_formats 工具:")
                try:
                    result = await session.call_tool("list_supported_formats", {})
                    print("✅ 工具调用成功!")
                    print(f"结果类型: {type(result)}")
                    if hasattr(result, 'content') and result.content:
                        print(f"内容: {result.content[0].text[:200]}...")
                    else:
                        print(f"结果: {result}")
                except Exception as e:
                    print(f"❌ 工具调用失败: {e}")
                
                print("\n✅ MCP服务器测试完成!")
                
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_mcp_server())