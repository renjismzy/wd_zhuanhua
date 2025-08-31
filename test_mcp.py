#!/usr/bin/env python3
"""
测试MCP服务器连接
"""

import asyncio
import json
import sys
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client

async def test_mcp_server():
    """测试MCP服务器连接"""
    try:
        # 启动MCP服务器进程
        from mcp.client.stdio import StdioServerParameters
        server_params = StdioServerParameters(
            command=sys.executable,
            args=["mcp_server_only.py"]
        )
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # 初始化连接
                await session.initialize()
                
                print("✅ MCP服务器连接成功!")
                
                # 列出工具
                tools = await session.list_tools()
                print(f"📋 可用工具: {len(tools.tools)}")
                for tool in tools.tools:
                    print(f"  - {tool.name}: {tool.description}")
                
                # 测试list_supported_formats工具
                print("\n🔧 测试 list_supported_formats 工具...")
                result = await session.call_tool("list_supported_formats", {})
                print(f"结果: {result.content[0].text if result.content else 'No content'}")
                
                print("\n✅ MCP服务器测试完成!")
                
    except Exception as e:
        print(f"❌ MCP服务器测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_mcp_server())