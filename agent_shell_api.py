import asyncio
import websockets
import json
import time
from security_utils import SecurityManager

async def execute_command(ip: str, command: str, port: int = 8765) -> dict:
    """
    在指定IP的服务器上执行加密命令
    
    Args:
        ip (str): 目标服务器IP地址
        command (str): 要执行的PowerShell命令
        port (int, optional): 服务器端口号，默认为8765
        
    Returns:
        dict: 命令执行的响应结果
    """
    uri = f"ws://{ip}:{port}"
    security_manager = SecurityManager(is_server=False)
    
    try:
        # 加载服务器公钥
        security_manager.load_client_public_key()
        
        async with websockets.connect(uri) as websocket:
            # 生成会话密钥并用RSA公钥加密
            session_key = security_manager.generate_session_key()
            encrypted_session_key = security_manager.encrypt_session_key(session_key)
            await websocket.send(encrypted_session_key)
            
            # 保存会话密钥用于后续通信
            security_manager.session_key = session_key
            
            # 等待服务器确认
            ready_response = await websocket.recv()
            ready_data = json.loads(ready_response)
            if ready_data.get("status") != "ready":
                raise Exception("服务器未就绪")
            
            # 创建加密消息
            message = {
                "type": "powershell",
                "command": command
            }
            secure_message = security_manager.create_secure_message(message)
            
            # 发送加密消息
            await websocket.send(json.dumps(secure_message))
            
            # 接收并解密响应
            encrypted_response = await websocket.recv()
            response_data = json.loads(encrypted_response)
            
            # 解密并验证响应
            return security_manager.decrypt_message(response_data)
            
    except Exception as e:
        return {"error": f"执行命令时出错: {str(e)}"}

def run_command(ip: str, command: str, port: int = 8765) -> dict:
    """
    同步方式执行加密命令的包装函数
    
    Args:
        ip (str): 目标服务器IP地址
        command (str): 要执行的PowerShell命令
        port (int, optional): 服务器端口号，默认为8765
        
    Returns:
        dict: 命令执行的响应结果
    """
    return asyncio.run(execute_command(ip, command, port))

# 使用示例
if __name__ == "__main__":
    # 示例：执行加密命令
    result = run_command("127.0.0.1", "wmic logicaldisk get size,freespace,caption")
    print(json.dumps(result, indent=2, ensure_ascii=False))