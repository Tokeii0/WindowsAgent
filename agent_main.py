import asyncio
import websockets
import json
import subprocess
import platform
import psutil
import logging
import time
from datetime import datetime
from security_utils import SecurityManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('agent.log'),
        logging.StreamHandler()
    ]
)

class WindowsAgent:
    def __init__(self, host="0.0.0.0", port=8765):
        self.host = host
        self.port = port
        self.system_info = self._get_system_info()
        # 初始化服务器端安全管理器
        self.security_manager = SecurityManager(is_server=True)
        # 加载服务器私钥
        self.security_manager.load_server_private_key()
        logging.info(f"Agent初始化完成: {self.system_info}")

    def _get_system_info(self):
        """获取系统信息"""
        return {
            "hostname": platform.node(),
            "system": platform.system(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor()
        }

    async def execute_command(self, command):
        """执行PowerShell命令"""
        try:
            process = subprocess.Popen(
                ["powershell", "-Command", command],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate()
            return {
                "success": process.returncode == 0,
                "stdout": stdout,
                "stderr": stderr,
                "returncode": process.returncode,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def get_system_metrics(self):
        """获取系统指标"""
        try:
            return {
                "success": True,
                "data": {
                    "cpu_percent": psutil.cpu_percent(interval=1),
                    "memory": psutil.virtual_memory()._asdict(),
                    "disk": {disk.device: psutil.disk_usage(disk.mountpoint)._asdict() 
                            for disk in psutil.disk_partitions() 
                            if disk.fstype != ""},
                    "timestamp": datetime.now().isoformat()
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def handle_client(self, websocket):
        """处理客户端连接"""
        client_info = websocket.remote_address
        logging.info(f"新的客户端连接: {client_info}")
        
        try:
            # 接收加密的会话密钥
            encrypted_session_key = await websocket.recv()
            session_key = self.security_manager.decrypt_session_key(encrypted_session_key)
            self.security_manager.session_key = session_key
            
            logging.info("安全会话已建立")
            
            # 发送确认消息
            await websocket.send(json.dumps({"status": "ready"}))
            
            async for message in websocket:
                try:
                    # 解析加密消息
                    secure_data = json.loads(message)
                    
                    # 解密并验证消息
                    data = self.security_manager.decrypt_message(secure_data)
                    
                    command_type = data.get("type")
                    command = data.get("command")
                    
                    logging.info(f"收到命令: {command_type} - {command}")
                    
                    # 执行命令并获取结果
                    if command_type == "powershell":
                        result = await self.execute_command(command)
                    elif command_type == "metrics":
                        result = await self.get_system_metrics()
                    elif command_type == "info":
                        result = {"success": True, "data": self.system_info}
                    else:
                        result = {"success": False, "error": "未知的命令类型"}
                    
                    # 创建加密响应
                    secure_response = self.security_manager.create_secure_message(result)
                    await websocket.send(json.dumps(secure_response))
                    
                except Exception as e:
                    error_response = self.security_manager.create_secure_message({
                        "success": False,
                        "error": str(e)
                    })
                    await websocket.send(json.dumps(error_response))
                    logging.error(f"处理消息时出错: {str(e)}")
        
        except Exception as e:
            logging.error(f"WebSocket连接错误: {str(e)}")
        finally:
            logging.info(f"客户端断开连接: {client_info}")

    async def start(self):
        """启动WebSocket服务器"""
        server = await websockets.serve(self.handle_client, self.host, self.port)
        logging.info(f"Agent服务器启动在 {self.host}:{self.port}")
        await server.wait_closed()

def main():
    agent = WindowsAgent()
    asyncio.run(agent.start())

if __name__ == "__main__":
    main()
