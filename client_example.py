#!/usr/bin/env python3
"""
Client Examples for Document Conversion MCP Server

Provides example clients for MCP, SSE, and REST API interactions.
"""

import asyncio
import json
import logging
import sys
from typing import Any, Dict, Optional

import aiohttp

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentConversionClient:
    """MCP客户端示例"""
    
    def __init__(self, server_command: str = "python", server_args: list = None):
        if server_args is None:
            server_args = ["main.py"]
        self.server_command = server_command
        self.server_args = server_args
    
    async def connect_and_convert(self, source_format: str, target_format: str, content: str):
        """连接到MCP服务器并执行转换"""
        try:
            # 注意：这里需要实际的MCP客户端库
            # 由于MCP库的具体实现可能不同，这里提供一个概念性的示例
            logger.info(f"Connecting to MCP server: {self.server_command} {' '.join(self.server_args)}")
            
            # 模拟MCP连接和工具调用
            logger.info(f"Converting {source_format} to {target_format}")
            logger.info(f"Content preview: {content[:100]}...")
            
            # 这里应该是实际的MCP客户端代码
            # 例如：
            # from mcp.client.stdio import stdio_client
            # from mcp import StdioServerParameters
            # 
            # server_params = StdioServerParameters(
            #     command=self.server_command,
            #     args=self.server_args
            # )
            # 
            # async with stdio_client(server_params) as session:
            #     await session.initialize()
            #     
            #     result = await session.call_tool("convert_document", {
            #         "source_format": source_format,
            #         "target_format": target_format,
            #         "content": content
            #     })
            #     
            #     return result
            
            # 模拟返回结果
            return {
                "success": True,
                "message": f"Document converted from {source_format} to {target_format}",
                "job_id": "mock-job-id-12345"
            }
            
        except Exception as e:
            logger.error(f"MCP client error: {e}")
            return {"success": False, "error": str(e)}


class SSEClient:
    """SSE客户端示例"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
    
    async def connect(self):
        """连接到SSE端点"""
        self.session = aiohttp.ClientSession()
    
    async def disconnect(self):
        """断开连接"""
        if self.session:
            await self.session.close()
    
    async def listen_events(self, duration: int = 60):
        """监听SSE事件"""
        if not self.session:
            await self.connect()
        
        try:
            logger.info(f"Connecting to SSE endpoint: {self.base_url}/events")
            
            async with self.session.get(f"{self.base_url}/events") as response:
                if response.status != 200:
                    logger.error(f"SSE connection failed: {response.status}")
                    return
                
                logger.info("SSE connection established, listening for events...")
                
                start_time = asyncio.get_event_loop().time()
                
                async for line in response.content:
                    # 检查超时
                    if asyncio.get_event_loop().time() - start_time > duration:
                        logger.info("Listening duration exceeded, stopping...")
                        break
                    
                    line = line.decode('utf-8').strip()
                    
                    if line.startswith('data: '):
                        try:
                            data = json.loads(line[6:])
                            await self._handle_event(data)
                        except json.JSONDecodeError as e:
                            logger.warning(f"Failed to parse SSE data: {e}")
                    elif line.startswith('event: '):
                        event_type = line[7:]
                        logger.debug(f"Event type: {event_type}")
                    elif line.startswith('id: '):
                        event_id = line[4:]
                        logger.debug(f"Event ID: {event_id}")
                    elif line == "":
                        # 空行表示事件结束
                        pass
                    elif line.startswith(': '):
                        # 注释行（心跳等）
                        logger.debug(f"SSE comment: {line[2:]}")
                
        except Exception as e:
            logger.error(f"SSE client error: {e}")
        finally:
            await self.disconnect()
    
    async def _handle_event(self, data: Dict[str, Any]):
        """处理SSE事件"""
        event_type = data.get('type', 'unknown')
        
        if event_type == 'connected':
            logger.info(f"Connected to SSE server: {data.get('message')}")
        elif event_type == 'heartbeat':
            logger.debug(f"Heartbeat received at {data.get('timestamp')}")
        elif event_type == 'conversion_started':
            logger.info(f"Conversion started - Job ID: {data.get('job_id')}")
        elif event_type == 'conversion_progress':
            job_id = data.get('job_id')
            progress = data.get('progress')
            status = data.get('status')
            logger.info(f"Conversion progress - Job {job_id}: {progress}% ({status})")
        elif event_type == 'conversion_complete':
            job_id = data.get('job_id')
            logger.info(f"Conversion completed - Job ID: {job_id}")
            logger.info(f"Result: {data.get('result')}")
        elif event_type == 'conversion_error':
            job_id = data.get('job_id')
            error = data.get('error')
            logger.error(f"Conversion failed - Job {job_id}: {error}")
        else:
            logger.info(f"Received event: {event_type} - {data}")


class RestApiClient:
    """REST API客户端示例"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
    
    async def connect(self):
        """创建HTTP会话"""
        self.session = aiohttp.ClientSession()
    
    async def disconnect(self):
        """关闭HTTP会话"""
        if self.session:
            await self.session.close()
    
    async def convert_document(self, source_format: str, target_format: str, content: str) -> Dict[str, Any]:
        """转换文档"""
        if not self.session:
            await self.connect()
        
        try:
            data = {
                "source_format": source_format,
                "target_format": target_format,
                "content": content
            }
            
            logger.info(f"Converting document via REST API: {source_format} -> {target_format}")
            
            async with self.session.post(f"{self.base_url}/convert", json=data) as response:
                result = await response.json()
                
                if response.status == 200:
                    logger.info("Conversion successful")
                    return result
                else:
                    logger.error(f"Conversion failed: {response.status} - {result}")
                    return result
                    
        except Exception as e:
            logger.error(f"REST API error: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_supported_formats(self) -> Dict[str, Any]:
        """获取支持的格式"""
        if not self.session:
            await self.connect()
        
        try:
            async with self.session.get(f"{self.base_url}/formats") as response:
                return await response.json()
        except Exception as e:
            logger.error(f"Failed to get formats: {e}")
            return {"error": str(e)}
    
    async def get_conversion_status(self, job_id: str) -> Dict[str, Any]:
        """获取转换状态"""
        if not self.session:
            await self.connect()
        
        try:
            async with self.session.get(f"{self.base_url}/status/{job_id}") as response:
                return await response.json()
        except Exception as e:
            logger.error(f"Failed to get status: {e}")
            return {"error": str(e)}


async def demo_mcp_client():
    """MCP客户端演示"""
    logger.info("=== MCP Client Demo ===")
    
    client = DocumentConversionClient()
    
    # 示例转换
    content = "# Hello World\n\nThis is a **markdown** document with *italic* text."
    result = await client.connect_and_convert("md", "html", content)
    
    logger.info(f"MCP Result: {result}")


async def demo_sse_client():
    """SSE客户端演示"""
    logger.info("=== SSE Client Demo ===")
    
    client = SSEClient()
    
    # 监听事件30秒
    await client.listen_events(duration=30)


async def demo_rest_api():
    """REST API客户端演示"""
    logger.info("=== REST API Client Demo ===")
    
    client = RestApiClient()
    
    try:
        # 获取支持的格式
        formats = await client.get_supported_formats()
        logger.info(f"Supported formats: {formats}")
        
        # 转换文档
        content = "# Hello World\n\nThis is a **markdown** document."
        result = await client.convert_document("md", "html", content)
        logger.info(f"Conversion result: {result}")
        
    finally:
        await client.disconnect()


async def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("Usage: python client_example.py <mode>")
        print("Modes: mcp, sse, api")
        return
    
    mode = sys.argv[1].lower()
    
    if mode == "mcp":
        await demo_mcp_client()
    elif mode == "sse":
        await demo_sse_client()
    elif mode == "api":
        await demo_rest_api()
    else:
        print(f"Unknown mode: {mode}")
        print("Available modes: mcp, sse, api")


if __name__ == "__main__":
    asyncio.run(main())