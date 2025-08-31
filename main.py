#!/usr/bin/env python3
"""
Document Conversion MCP Server with SSE Support

A Model Context Protocol (MCP) server that provides document conversion capabilities
with Server-Sent Events (SSE) support for real-time communication.
"""

import asyncio
import json
import logging
import mimetypes
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import aiofiles
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from mcp.server import Server
from mcp.types import (
    CallToolResult,
    TextContent,
    Tool,
)
from pydantic import BaseModel
from sse_starlette import EventSourceResponse

from document_converter import DocumentConverter
from sse_manager import SSEManager

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="Document Conversion MCP Server",
    description="MCP server for document conversion with SSE support",
    version="0.1.0"
)

# 初始化组件
document_converter = DocumentConverter()
sse_manager = SSEManager()

# MCP服务器实例
mcp_server = Server("document-conversion-server")


class ConversionRequest(BaseModel):
    """文档转换请求模型"""
    source_format: str
    target_format: str
    content: Optional[str] = None
    file_path: Optional[str] = None


class ConversionResponse(BaseModel):
    """文档转换响应模型"""
    success: bool
    content: Optional[str] = None
    file_path: Optional[str] = None
    error: Optional[str] = None


@mcp_server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """列出可用的工具"""
    return [
        Tool(
            name="convert_document",
            description="Convert documents between different formats (PDF, DOCX, MD, TXT, HTML)",
            inputSchema={
                "type": "object",
                "properties": {
                    "source_format": {
                        "type": "string",
                        "description": "Source document format (pdf, docx, md, txt, html)"
                    },
                    "target_format": {
                        "type": "string",
                        "description": "Target document format (pdf, docx, md, txt, html)"
                    },
                    "content": {
                        "type": "string",
                        "description": "Document content (for text-based formats)"
                    },
                    "file_path": {
                        "type": "string",
                        "description": "Path to source file (alternative to content)"
                    }
                },
                "required": ["source_format", "target_format"]
            }
        ),
        Tool(
            name="list_supported_formats",
            description="List all supported document formats for conversion",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_conversion_status",
            description="Get the status of a document conversion job",
            inputSchema={
                "type": "object",
                "properties": {
                    "job_id": {
                        "type": "string",
                        "description": "Conversion job ID"
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
        if name == "convert_document":
            return await handle_convert_document(arguments)
        elif name == "list_supported_formats":
            return await handle_list_supported_formats()
        elif name == "get_conversion_status":
            return await handle_get_conversion_status(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")
    except Exception as e:
        logger.error(f"Error handling tool call {name}: {e}")
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"Error: {str(e)}"
                )
            ],
            isError=True
        )


async def handle_convert_document(arguments: Dict[str, Any]) -> CallToolResult:
    """处理文档转换"""
    source_format = arguments.get("source_format")
    target_format = arguments.get("target_format")
    content = arguments.get("content")
    file_path = arguments.get("file_path")
    
    if not source_format or not target_format:
        raise ValueError("source_format and target_format are required")
    
    if not content and not file_path:
        raise ValueError("Either content or file_path must be provided")
    
    # 创建转换任务
    job_id = await document_converter.convert_async(
        source_format=source_format,
        target_format=target_format,
        content=content,
        file_path=file_path
    )
    
    # 通过SSE发送进度更新
    await sse_manager.send_event({
        "type": "conversion_started",
        "job_id": job_id,
        "source_format": source_format,
        "target_format": target_format
    })
    
    return CallToolResult(
        content=[
            TextContent(
                type="text",
                text=f"Document conversion started. Job ID: {job_id}"
            )
        ],
        isError=False
    )


async def handle_list_supported_formats() -> CallToolResult:
    """列出支持的格式"""
    formats = document_converter.get_supported_formats()
    return CallToolResult(
        content=[
            TextContent(
                type="text",
                text=f"Supported formats: {', '.join(formats)}"
            )
        ],
        isError=False
    )


async def handle_get_conversion_status(arguments: Dict[str, Any]) -> CallToolResult:
    """获取转换状态"""
    job_id = arguments.get("job_id")
    if not job_id:
        raise ValueError("job_id is required")
    
    status = await document_converter.get_job_status(job_id)
    return CallToolResult(
        content=[
            TextContent(
                type="text",
                text=json.dumps(status, indent=2)
            )
        ],
        isError=False
    )


# FastAPI路由
@app.post("/convert", response_model=ConversionResponse)
async def convert_document_api(
    source_format: str = Form(...),
    target_format: str = Form(...),
    content: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    """REST API端点用于文档转换"""
    try:
        if file:
            # 保存上传的文件
            temp_path = f"/tmp/{file.filename}"
            async with aiofiles.open(temp_path, 'wb') as f:
                content_bytes = await file.read()
                await f.write(content_bytes)
            
            job_id = await document_converter.convert_async(
                source_format=source_format,
                target_format=target_format,
                file_path=temp_path
            )
        else:
            job_id = await document_converter.convert_async(
                source_format=source_format,
                target_format=target_format,
                content=content
            )
        
        # 等待转换完成
        result = await document_converter.wait_for_completion(job_id)
        
        return ConversionResponse(
            success=result["success"],
            content=result.get("content"),
            file_path=result.get("file_path"),
            error=result.get("error")
        )
    
    except Exception as e:
        logger.error(f"Conversion error: {e}")
        return ConversionResponse(
            success=False,
            error=str(e)
        )


@app.get("/events")
async def stream_events():
    """SSE端点用于实时事件流"""
    return EventSourceResponse(sse_manager.event_stream())


@app.get("/formats")
async def list_formats():
    """列出支持的格式"""
    return {"formats": document_converter.get_supported_formats()}


@app.get("/status/{job_id}")
async def get_status(job_id: str):
    """获取转换任务状态"""
    return await document_converter.get_job_status(job_id)


async def run_mcp_server():
    """运行MCP服务器"""
    # 使用stdio传输
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await mcp_server.run(
            read_stream,
            write_stream,
            mcp_server.create_initialization_options()
        )


def main():
    """主函数"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--api":
        # 运行FastAPI服务器
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)
    else:
        # 运行MCP服务器
        asyncio.run(run_mcp_server())


if __name__ == "__main__":
    main()
