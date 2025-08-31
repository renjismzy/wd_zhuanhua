#!/usr/bin/env python3
"""
Pure MCP Server for Document Conversion

A clean Model Context Protocol (MCP) server implementation without HTTP components.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.types import (
    CallToolResult,
    TextContent,
    Tool,
)

from document_converter import DocumentConverter

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 初始化文档转换器
document_converter = DocumentConverter()

# MCP服务器实例
mcp_server = Server("document-conversion-server")


@mcp_server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """列出可用的工具"""
    return [
        Tool(
            name="list_supported_formats",
            description="List all supported document formats for conversion",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="convert_document",
            description="Convert a document from one format to another",
            inputSchema={
                "type": "object",
                "properties": {
                    "input_path": {
                        "type": "string",
                        "description": "Path to the input document"
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Path for the output document"
                    },
                    "target_format": {
                        "type": "string",
                        "description": "Target format for conversion (e.g., 'pdf', 'docx', 'html')"
                    }
                },
                "required": ["input_path", "output_path", "target_format"]
            }
        ),
        Tool(
            name="get_conversion_status",
            description="Get the status of a conversion job",
            inputSchema={
                "type": "object",
                "properties": {
                    "job_id": {
                        "type": "string",
                        "description": "The job ID returned from convert_document"
                    }
                },
                "required": ["job_id"]
            }
        )
    ]


@mcp_server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
    """处理工具调用"""
    try:
        if name == "list_supported_formats":
            return await handle_list_supported_formats()
        elif name == "convert_document":
            return await handle_convert_document(arguments)
        elif name == "get_conversion_status":
            return await handle_get_conversion_status(arguments)
        else:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Unknown tool: {name}")],
                isError=True
            )
    except Exception as e:
        logger.error(f"Error in tool call {name}: {str(e)}")
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error: {str(e)}")],
            isError=True
        )


async def handle_list_supported_formats() -> CallToolResult:
    """列出支持的格式"""
    formats = await document_converter.get_supported_formats()
    return CallToolResult(
        content=[TextContent(type="text", text=json.dumps(formats, indent=2))],
        isError=False
    )


async def handle_convert_document(arguments: Dict[str, Any]) -> CallToolResult:
    """转换文档"""
    input_path = arguments.get("input_path")
    output_path = arguments.get("output_path")
    target_format = arguments.get("target_format")
    
    if not all([input_path, output_path, target_format]):
        return CallToolResult(
            content=[TextContent(type="text", text="Missing required arguments: input_path, output_path, target_format")],
            isError=True
        )
    
    job_id = await document_converter.convert_document(
        input_path=input_path,
        output_path=output_path,
        target_format=target_format
    )
    
    result = {
        "job_id": job_id,
        "status": "started",
        "input_path": input_path,
        "output_path": output_path,
        "target_format": target_format
    }
    
    return CallToolResult(
        content=[TextContent(type="text", text=json.dumps(result, indent=2))],
        isError=False
    )


async def handle_get_conversion_status(arguments: Dict[str, Any]) -> CallToolResult:
    """获取转换状态"""
    job_id = arguments.get("job_id")
    
    if not job_id:
        return CallToolResult(
            content=[TextContent(type="text", text="Missing required argument: job_id")],
            isError=True
        )
    
    status = await document_converter.get_job_status(job_id)
    return CallToolResult(
        content=[TextContent(type="text", text=json.dumps(status, indent=2))],
        isError=False
    )


async def run_mcp_server():
    """运行MCP服务器"""
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await mcp_server.run(
            read_stream,
            write_stream,
            mcp_server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(run_mcp_server())