#!/usr/bin/env python3
"""
Configuration Module

Provides configuration management for the MCP server.
"""

import os
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class Config:
    """配置类"""
    
    # 服务器信息
    server_name: str = "document-conversion-server"
    server_version: str = "0.1.0"
    server_description: str = "MCP server for document conversion with SSE support"
    
    # API配置
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_debug: bool = False
    
    # 文件处理配置
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    temp_dir: str = "/tmp"
    allowed_extensions: List[str] = None
    
    # 文档转换配置
    conversion_timeout: int = 300  # 5分钟
    max_concurrent_conversions: int = 10
    cleanup_temp_files: bool = True
    
    # SSE配置
    sse_heartbeat_interval: int = 30  # 秒
    sse_connection_timeout: int = 3600  # 1小时
    sse_max_connections: int = 100
    
    # 日志配置
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_file: Optional[str] = None
    
    # 安全配置
    enable_cors: bool = True
    cors_origins: List[str] = None
    max_request_size: int = 100 * 1024 * 1024  # 100MB
    
    def __post_init__(self):
        """初始化后处理"""
        if self.allowed_extensions is None:
            self.allowed_extensions = ['.txt', '.md', '.html', '.pdf', '.docx', '.doc']
        
        if self.cors_origins is None:
            self.cors_origins = ["*"]
        
        # 从环境变量加载配置
        self._load_from_env()
    
    def _load_from_env(self):
        """从环境变量加载配置"""
        # 服务器配置
        self.server_name = os.getenv("SERVER_NAME", self.server_name)
        self.server_version = os.getenv("SERVER_VERSION", self.server_version)
        self.server_description = os.getenv("SERVER_DESCRIPTION", self.server_description)
        
        # API配置
        self.api_host = os.getenv("API_HOST", self.api_host)
        self.api_port = int(os.getenv("API_PORT", str(self.api_port)))
        self.api_debug = os.getenv("API_DEBUG", "false").lower() == "true"
        
        # 文件处理配置
        if os.getenv("MAX_FILE_SIZE"):
            self.max_file_size = int(os.getenv("MAX_FILE_SIZE")) * 1024 * 1024  # MB to bytes
        
        self.temp_dir = os.getenv("TEMP_DIR", self.temp_dir)
        
        if os.getenv("ALLOWED_EXTENSIONS"):
            self.allowed_extensions = os.getenv("ALLOWED_EXTENSIONS").split(",")
        
        # 文档转换配置
        self.conversion_timeout = int(os.getenv("CONVERSION_TIMEOUT", str(self.conversion_timeout)))
        self.max_concurrent_conversions = int(os.getenv("MAX_CONCURRENT_CONVERSIONS", str(self.max_concurrent_conversions)))
        self.cleanup_temp_files = os.getenv("CLEANUP_TEMP_FILES", "true").lower() == "true"
        
        # SSE配置
        self.sse_heartbeat_interval = int(os.getenv("SSE_HEARTBEAT_INTERVAL", str(self.sse_heartbeat_interval)))
        self.sse_connection_timeout = int(os.getenv("SSE_CONNECTION_TIMEOUT", str(self.sse_connection_timeout)))
        self.sse_max_connections = int(os.getenv("SSE_MAX_CONNECTIONS", str(self.sse_max_connections)))
        
        # 日志配置
        self.log_level = os.getenv("LOG_LEVEL", self.log_level)
        self.log_format = os.getenv("LOG_FORMAT", self.log_format)
        self.log_file = os.getenv("LOG_FILE")
        
        # 安全配置
        self.enable_cors = os.getenv("ENABLE_CORS", "true").lower() == "true"
        
        if os.getenv("CORS_ORIGINS"):
            self.cors_origins = os.getenv("CORS_ORIGINS").split(",")
        
        if os.getenv("MAX_REQUEST_SIZE"):
            self.max_request_size = int(os.getenv("MAX_REQUEST_SIZE")) * 1024 * 1024  # MB to bytes
    
    def get_supported_formats(self) -> Dict[str, Dict[str, bool]]:
        """获取支持的文档格式"""
        return {
            'txt': {'read': True, 'write': True, 'description': 'Plain text'},
            'md': {'read': True, 'write': True, 'description': 'Markdown'},
            'html': {'read': True, 'write': True, 'description': 'HTML'},
            'pdf': {'read': True, 'write': True, 'description': 'PDF'},
            'docx': {'read': True, 'write': True, 'description': 'Microsoft Word (DOCX)'},
            'doc': {'read': True, 'write': False, 'description': 'Microsoft Word (DOC) - Read only'}
        }
    
    def is_file_allowed(self, filename: str) -> bool:
        """检查文件是否允许"""
        if not filename:
            return False
        
        # 检查扩展名
        ext = os.path.splitext(filename.lower())[1]
        return ext in self.allowed_extensions
    
    def get_temp_path(self, filename: str) -> str:
        """获取临时文件路径"""
        import tempfile
        import uuid
        
        # 生成唯一的临时文件名
        name, ext = os.path.splitext(filename)
        temp_name = f"{name}_{uuid.uuid4().hex[:8]}{ext}"
        
        return os.path.join(self.temp_dir, temp_name)
    
    def validate(self) -> List[str]:
        """验证配置"""
        errors = []
        
        # 验证端口
        if not (1 <= self.api_port <= 65535):
            errors.append(f"Invalid API port: {self.api_port}")
        
        # 验证文件大小
        if self.max_file_size <= 0:
            errors.append(f"Invalid max file size: {self.max_file_size}")
        
        # 验证超时时间
        if self.conversion_timeout <= 0:
            errors.append(f"Invalid conversion timeout: {self.conversion_timeout}")
        
        # 验证并发数
        if self.max_concurrent_conversions <= 0:
            errors.append(f"Invalid max concurrent conversions: {self.max_concurrent_conversions}")
        
        # 验证SSE配置
        if self.sse_heartbeat_interval <= 0:
            errors.append(f"Invalid SSE heartbeat interval: {self.sse_heartbeat_interval}")
        
        if self.sse_connection_timeout <= 0:
            errors.append(f"Invalid SSE connection timeout: {self.sse_connection_timeout}")
        
        # 验证临时目录
        if not os.path.exists(self.temp_dir):
            try:
                os.makedirs(self.temp_dir, exist_ok=True)
            except Exception as e:
                errors.append(f"Cannot create temp directory {self.temp_dir}: {e}")
        
        return errors
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'server': {
                'name': self.server_name,
                'version': self.server_version,
                'description': self.server_description
            },
            'api': {
                'host': self.api_host,
                'port': self.api_port,
                'debug': self.api_debug
            },
            'file_handling': {
                'max_file_size': self.max_file_size,
                'temp_dir': self.temp_dir,
                'allowed_extensions': self.allowed_extensions
            },
            'conversion': {
                'timeout': self.conversion_timeout,
                'max_concurrent': self.max_concurrent_conversions,
                'cleanup_temp_files': self.cleanup_temp_files
            },
            'sse': {
                'heartbeat_interval': self.sse_heartbeat_interval,
                'connection_timeout': self.sse_connection_timeout,
                'max_connections': self.sse_max_connections
            },
            'logging': {
                'level': self.log_level,
                'format': self.log_format,
                'file': self.log_file
            },
            'security': {
                'enable_cors': self.enable_cors,
                'cors_origins': self.cors_origins,
                'max_request_size': self.max_request_size
            }
        }


# 全局配置实例
config = Config()