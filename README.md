# WindowsAgent

这是一个使用RSA加密和会话密钥保护的远程PowerShell命令执行系统，让您能够安全地在远程Windows服务器上执行PowerShell命令并获取结果。

### 核心组件
1. **服务器端** (`agent_main.py`)
   - 负责接收和执行命令
   - 管理RSA私钥
   - 处理WebSocket连接

2. **客户端** (`agent_shell_api.py`)
   - 提供命令发送接口
   - 管理RSA公钥
   - 处理加密通信

3. **安全管理器** (`security_utils.py`)
   - 处理RSA密钥对管理
   - 实现会话密钥加密
   - 提供消息加密和验证

4. **密钥生成器** (`generate_keys.py`)
   - 生成RSA密钥对
   - 创建部署包
   - 分发公钥和私钥

## Agent流程


![_- visual selection (1)](https://github.com/user-attachments/assets/0ebc3c28-fea3-4692-82bb-d4f8d0995b97)


## 部署说明

### 1. 生成部署包
```bash
python generate_keys.py
```
这将创建两个部署包：
- `deployment_keys/server/`：服务器端文件
- `deployment_keys/client/`：客户端文件

### 2. 服务器部署
1. 将服务器部署包内容复制到目标目录
2. 确保目录结构：
   ```
   server/
   ├── agent_main.py (或 server.exe)
   ├── security_utils.py
   └── keys/
       └── private_key.pem
   ```
3. 启动服务器：
   ```bash
   python agent_main.py
   # 或直接运行 server.exe
   ```

### 3. 客户端部署
1. 将客户端部署包内容复制到目标目录
2. 确保目录结构：
   ```
   client/
   ├── agent_shell_api.py (或 client.exe)
   ├── security_utils.py
   └── keys/
       └── public_key.pem
   ```

## 使用方法

### Python环境
```python
from agent_shell_api import run_command

# 执行单条命令
result = run_command("服务器IP", "Get-Date")
print(result)

# 执行PowerShell命令
result = run_command("服务器IP", "Get-Process | Select-Object Name,CPU")
print(result)
```

### 可执行文件环境
1. 确保exe文件旁边有keys目录和对应的密钥文件
2. 按照API文档调用exe文件

## 注意事项

1. **密钥安全**
   - 私钥只能部署在服务器端
   - 公钥可以分发给客户端
   - 定期更换密钥对

2. **部署检查**
   - 确保密钥目录权限正确
   - 验证WebSocket端口是否开放
   - 测试连接是否加密

3. **运行环境**
   - 支持Python 3.6+
   - 需要安装依赖：cryptography, websockets
   - 如果是exe，确保密钥目录在正确位置

## 错误处理

1. **常见错误**
   - "找不到密钥文件"：检查keys目录和密钥文件
   - "连接被拒绝"：检查服务器是否运行，端口是否开放
   - "签名验证失败"：检查密钥是否匹配

2. **调试方法**
   - 检查日志输出
   - 验证密钥文件权限
   - 确认网络连接状态

## 安全建议

1. 使用防火墙限制访问
2. 定期更换密钥对
3. 监控异常连接
4. 及时更新系统补丁
