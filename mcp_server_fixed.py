#!/usr/bin/env python3
"""
Fixed MCP Server for Document Conversion

A working MCP server implementation that avoids the CallToolResult serialization bug.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List

from mcp.server import Server
from mcp.types import (
    Tool,
    TextContent,
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
async def handle_call_tool(name: str, arguments: Dict[str, Any]):
    """处理工具调用 - 返回简单的内容而不是CallToolResult对象"""
    try:
        if name == "list_supported_formats":
            return await handle_list_supported_formats()
        elif name == "convert_document":
            return await handle_convert_document(arguments)
        elif name == "get_conversion_status":
            return await handle_get_conversion_status(arguments)
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    except Exception as e:
        logger.error(f"Error in tool call {name}: {str(e)}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def handle_list_supported_formats():
    """列出支持的格式"""
    try:
        formats = document_converter.get_supported_formats()
        formats_info = {
            "supported_formats": formats,
            "format_details": document_converter.supported_formats
        }
        return [TextContent(type="text", text=json.dumps(formats_info, indent=2))]
    except Exception as e:
        logger.error(f"Error listing supported formats: {str(e)}")
        return [TextContent(type="text", text=f"Error listing formats: {str(e)}")]


async def handle_convert_document(arguments: Dict[str, Any]):
    """转换文档"""
    try:
        input_path = arguments.get("input_path")
        output_path = arguments.get("output_path")
        target_format = arguments.get("target_format")
        
        if not all([input_path, output_path, target_format]):
            return [TextContent(type="text", text="Missing required arguments: input_path, output_path, target_format")]
        
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
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    except Exception as e:
        logger.error(f"Error converting document: {str(e)}")
        return [TextContent(type="text", text=f"Error converting document: {str(e)}")]


async def handle_get_conversion_status(arguments: Dict[str, Any]):
    """获取转换状态"""
    try:
        job_id = arguments.get("job_id")
        
        if not job_id:
            return [TextContent(type="text", text="Missing required argument: job_id")]
        
        status = await document_converter.get_job_status(job_id)
        return [TextContent(type="text", text=json.dumps(status, indent=2))]
    except Exception as e:
        logger.error(f"Error getting conversion status: {str(e)}")
        return [TextContent(type="text", text=f"Error getting status: {str(e)}")]


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