import os
import shutil
from security_utils import SecurityManager

def generate_deployment_keys(output_dir="deployment_keys"):
    """
    生成部署所需的密钥文件
    
    Args:
        output_dir: 输出目录，默认为 'deployment_keys'
    """
    # 清理或创建输出目录
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)
    
    # 创建服务器和客户端目录
    server_dir = os.path.join(output_dir, "server")
    client_dir = os.path.join(output_dir, "client")
    os.makedirs(server_dir)
    os.makedirs(client_dir)
    
    # 生成密钥对
    print("正在生成RSA密钥对...")
    security_manager = SecurityManager(keys_dir="temp_keys")
    security_manager.generate_and_save_server_keys()
    
    # 移动密钥到对应目录
    temp_private_key = os.path.join("temp_keys", "private_key.pem")
    temp_public_key = os.path.join("temp_keys", "public_key.pem")
    
    # 创建服务器部署包
    server_keys_dir = os.path.join(server_dir, "keys")
    os.makedirs(server_keys_dir)
    shutil.copy2(temp_private_key, os.path.join(server_keys_dir, "private_key.pem"))
    
    # 创建客户端部署包
    client_keys_dir = os.path.join(client_dir, "keys")
    os.makedirs(client_keys_dir)
    shutil.copy2(temp_public_key, os.path.join(client_keys_dir, "public_key.pem"))
    
    # 复制必要的代码文件
    # 服务器文件
    shutil.copy2("agent_main.py", server_dir)
    shutil.copy2("security_utils.py", server_dir)
    
    # 客户端文件
    shutil.copy2("agent_shell_api.py", client_dir)
    shutil.copy2("security_utils.py", client_dir)
    
    # 清理临时文件
    shutil.rmtree("temp_keys")
    
    # 创建说明文件
    with open(os.path.join(server_dir, "README.txt"), "w", encoding="utf-8") as f:
        f.write("""服务器部署说明：
1. 将所有文件复制到服务器的目标目录
2. 确保 keys 目录与可执行文件在同一目录下，并包含 private_key.pem
3. 如果是Python环境：
   运行命令：python agent_main.py
4. 如果是打包为exe：
   直接运行exe文件即可

注意：
- 请妥善保管私钥文件
- 不要将私钥分享给任何人
- 建议设置适当的文件权限
""")
    
    with open(os.path.join(client_dir, "README.txt"), "w", encoding="utf-8") as f:
        f.write("""客户端使用说明：
1. 将所有文件复制到客户端目标目录
2. 确保 keys 目录与可执行文件在同一目录下，并包含 public_key.pem
3. 如果是Python环境：
   from agent_shell_api import run_command
   result = run_command("服务器IP", "要执行的命令")

4. 如果是打包为exe：
   - 确保keys目录与exe文件在同一目录
   - 按照API文档调用exe
""")
    
    print(f"\n部署文件已生成在 {output_dir} 目录下：")
    print(f"服务器部署包：{server_dir}")
    print(f"客户端部署包：{client_dir}")
    print("\n请按照每个目录中的 README.txt 进行部署。")
    print("\n重要提示：")
    print("1. 打包为exe时，确保keys目录与exe文件在同一目录")
    print("2. 不要将private_key.pem包含在客户端exe中")

if __name__ == "__main__":
    generate_deployment_keys()
