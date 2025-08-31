#!/usr/bin/env python3
"""
SSE Manager Module

Provides Server-Sent Events (SSE) management for real-time communication.
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, asdict
from typing import Any, AsyncGenerator, Dict, List, Optional, Set
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class SSEEvent:
    """SSE事件数据类"""
    event: str
    data: Dict[str, Any]
    id: Optional[str] = None
    retry: Optional[int] = None
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class SSEConnection:
    """SSE连接类"""
    
    def __init__(self, connection_id: str):
        self.connection_id = connection_id
        self.queue: asyncio.Queue = asyncio.Queue()
        self.connected = True
        self.last_heartbeat = time.time()
        self.created_at = datetime.now()
    
    async def send_event(self, event: SSEEvent):
        """发送事件到连接"""
        if self.connected:
            try:
                await self.queue.put(event)
            except Exception as e:
                logger.error(f"Error sending event to connection {self.connection_id}: {e}")
                self.connected = False
    
    async def get_event(self) -> Optional[SSEEvent]:
        """获取事件（非阻塞）"""
        try:
            return self.queue.get_nowait()
        except asyncio.QueueEmpty:
            return None
    
    async def wait_for_event(self, timeout: float = 30.0) -> Optional[SSEEvent]:
        """等待事件（阻塞）"""
        try:
            return await asyncio.wait_for(self.queue.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None
    
    def disconnect(self):
        """断开连接"""
        self.connected = False
    
    def update_heartbeat(self):
        """更新心跳时间"""
        self.last_heartbeat = time.time()


class SSEManager:
    """SSE管理器"""
    
    def __init__(self, heartbeat_interval: int = 30, connection_timeout: int = 3600):
        self.connections: Dict[str, SSEConnection] = {}
        self.heartbeat_interval = heartbeat_interval
        self.connection_timeout = connection_timeout
        self._cleanup_task = None
        self._started = False
    
    def _start_cleanup_task(self):
        """启动清理任务"""
        if not self._started and (self._cleanup_task is None or self._cleanup_task.done()):
            try:
                self._cleanup_task = asyncio.create_task(self._cleanup_connections())
                self._started = True
            except RuntimeError:
                # 没有运行的事件循环，稍后再启动
                pass
    
    async def _cleanup_connections(self):
        """清理过期连接"""
        while True:
            try:
                current_time = time.time()
                expired_connections = []
                
                for conn_id, connection in self.connections.items():
                    if (current_time - connection.last_heartbeat > self.connection_timeout or
                        not connection.connected):
                        expired_connections.append(conn_id)
                
                for conn_id in expired_connections:
                    logger.info(f"Cleaning up expired connection: {conn_id}")
                    await self.disconnect(conn_id)
                
                await asyncio.sleep(60)  # 每分钟清理一次
                
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
                await asyncio.sleep(60)
    
    async def create_connection(self, connection_id: Optional[str] = None) -> str:
        """创建新的SSE连接"""
        # 确保清理任务已启动
        if not self._started:
            self._start_cleanup_task()
        
        if connection_id is None:
            import uuid
            connection_id = str(uuid.uuid4())
        
        connection = SSEConnection(connection_id)
        self.connections[connection_id] = connection
        
        logger.info(f"Created SSE connection: {connection_id}")
        
        # 发送欢迎消息
        welcome_event = SSEEvent(
            event="connection",
            data={
                "type": "connected",
                "connection_id": connection_id,
                "message": "SSE connection established"
            }
        )
        await connection.send_event(welcome_event)
        
        return connection_id
    
    async def disconnect(self, connection_id: str):
        """断开连接"""
        if connection_id in self.connections:
            connection = self.connections[connection_id]
            connection.disconnect()
            del self.connections[connection_id]
            logger.info(f"Disconnected SSE connection: {connection_id}")
    
    async def send_event(
        self,
        data: Dict[str, Any],
        event: str = "message",
        connection_id: Optional[str] = None,
        event_id: Optional[str] = None
    ):
        """发送事件到指定连接或所有连接"""
        sse_event = SSEEvent(
            event=event,
            data=data,
            id=event_id
        )
        
        if connection_id:
            # 发送到指定连接
            if connection_id in self.connections:
                await self.connections[connection_id].send_event(sse_event)
            else:
                logger.warning(f"Connection not found: {connection_id}")
        else:
            # 广播到所有连接
            for connection in self.connections.values():
                await connection.send_event(sse_event)
    
    async def send_heartbeat(self, connection_id: Optional[str] = None):
        """发送心跳"""
        heartbeat_data = {
            "type": "heartbeat",
            "timestamp": datetime.now().isoformat()
        }
        
        await self.send_event(
            data=heartbeat_data,
            event="heartbeat",
            connection_id=connection_id
        )
    
    async def send_conversion_progress(
        self,
        job_id: str,
        progress: int,
        status: str,
        connection_id: Optional[str] = None
    ):
        """发送转换进度事件"""
        progress_data = {
            "type": "conversion_progress",
            "job_id": job_id,
            "progress": progress,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.send_event(
            data=progress_data,
            event="progress",
            connection_id=connection_id
        )
    
    async def send_conversion_complete(
        self,
        job_id: str,
        result: Dict[str, Any],
        connection_id: Optional[str] = None
    ):
        """发送转换完成事件"""
        complete_data = {
            "type": "conversion_complete",
            "job_id": job_id,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.send_event(
            data=complete_data,
            event="complete",
            connection_id=connection_id
        )
    
    async def send_conversion_error(
        self,
        job_id: str,
        error: str,
        connection_id: Optional[str] = None
    ):
        """发送转换错误事件"""
        error_data = {
            "type": "conversion_error",
            "job_id": job_id,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.send_event(
            data=error_data,
            event="error",
            connection_id=connection_id
        )
    
    def get_connection_count(self) -> int:
        """获取活跃连接数"""
        return len(self.connections)
    
    def get_connection_info(self) -> List[Dict[str, Any]]:
        """获取连接信息"""
        info = []
        for conn_id, connection in self.connections.items():
            info.append({
                "connection_id": conn_id,
                "connected": connection.connected,
                "created_at": connection.created_at.isoformat(),
                "last_heartbeat": datetime.fromtimestamp(connection.last_heartbeat).isoformat(),
                "queue_size": connection.queue.qsize()
            })
        return info
    
    async def event_stream(self, connection_id: Optional[str] = None) -> AsyncGenerator[str, None]:
        """生成SSE事件流"""
        if connection_id is None:
            connection_id = await self.create_connection()
        
        connection = self.connections.get(connection_id)
        if not connection:
            return
        
        try:
            last_heartbeat = time.time()
            
            while connection.connected:
                # 发送心跳
                current_time = time.time()
                if current_time - last_heartbeat >= self.heartbeat_interval:
                    await self.send_heartbeat(connection_id)
                    last_heartbeat = current_time
                
                # 获取事件
                event = await connection.wait_for_event(timeout=5.0)
                
                if event:
                    connection.update_heartbeat()
                    yield self._format_sse_event(event)
                else:
                    # 发送保持连接的注释
                    yield ": keep-alive\n\n"
                
        except Exception as e:
            logger.error(f"Error in event stream for connection {connection_id}: {e}")
        finally:
            await self.disconnect(connection_id)
    
    def _format_sse_event(self, event: SSEEvent) -> str:
        """格式化SSE事件"""
        lines = []
        
        if event.id:
            lines.append(f"id: {event.id}")
        
        if event.event:
            lines.append(f"event: {event.event}")
        
        if event.retry:
            lines.append(f"retry: {event.retry}")
        
        # 数据可能包含多行
        data_str = json.dumps(event.data, ensure_ascii=False)
        for line in data_str.split('\n'):
            lines.append(f"data: {line}")
        
        lines.append("")  # 空行表示事件结束
        lines.append("")  # 额外的空行
        
        return "\n".join(lines)
    
    async def shutdown(self):
        """关闭SSE管理器"""
        logger.info("Shutting down SSE manager")
        
        # 断开所有连接
        connection_ids = list(self.connections.keys())
        for conn_id in connection_ids:
            await self.disconnect(conn_id)
        
        # 取消清理任务
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        logger.info("SSE manager shutdown complete")