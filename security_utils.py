import os
import sys
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.fernet import Fernet
from base64 import b64encode, b64decode
import json
import time
import hmac
import hashlib

def get_base_path():
    """获取基础路径，兼容exe和普通Python环境"""
    if getattr(sys, 'frozen', False):
        # 如果是打包后的exe
        return os.path.dirname(sys.executable)
    else:
        # 如果是普通Python环境
        return os.path.dirname(os.path.abspath(__file__))

class SecurityManager:
    def __init__(self, keys_dir="keys", is_server=False):
        self.private_key = None
        self.public_key = None
        self.session_key = None
        self.hmac_key = b"lovelyOperations"
        self.timestamp_validity = 300
        # 使用绝对路径
        self.keys_dir = os.path.join(get_base_path(), keys_dir)
        self.is_server = is_server
        
        # 确保密钥目录存在
        if not os.path.exists(self.keys_dir):
            os.makedirs(self.keys_dir)

    def generate_and_save_server_keys(self):
        """仅在服务器首次部署时使用，生成并保存密钥对"""
        # 生成新密钥对
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        self.public_key = self.private_key.public_key()
        
        # 保存私钥（仅在服务器上）
        private_key_path = os.path.join(self.keys_dir, "private_key.pem")
        with open(private_key_path, "wb") as f:
            f.write(self.private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        # 保存公钥（用于分发给客户端）
        public_key_path = os.path.join(self.keys_dir, "public_key.pem")
        with open(public_key_path, "wb") as f:
            f.write(self.get_public_key_pem())
        
        print(f"密钥对已生成：\n私钥保存在：{private_key_path}\n公钥保存在：{public_key_path}")
        print("请将私钥安全地传输到服务器，并将公钥分发给客户端。")

    def load_server_private_key(self):
        """服务器加载私钥"""
        if not self.is_server:
            raise ValueError("此方法仅供服务器使用")
        
        private_key_path = os.path.join(self.keys_dir, "private_key.pem")
        if not os.path.exists(private_key_path):
            raise FileNotFoundError("找不到服务器私钥文件，请先生成密钥对并安全传输")
        
        with open(private_key_path, "rb") as f:
            self.private_key = serialization.load_pem_private_key(
                f.read(),
                password=None
            )

    def load_client_public_key(self):
        """客户端加载服务器公钥"""
        if self.is_server:
            raise ValueError("此方法仅供客户端使用")
        
        public_key_path = os.path.join(self.keys_dir, "public_key.pem")
        if not os.path.exists(public_key_path):
            raise FileNotFoundError("找不到服务器公钥文件，请从安全渠道获取服务器公钥")
        
        with open(public_key_path, "rb") as f:
            self.public_key = serialization.load_pem_public_key(f.read())

    def get_public_key_pem(self):
        """获取PEM格式的公钥"""
        if not self.public_key:
            raise ValueError("公钥未加载")
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

    def generate_session_key(self):
        """生成新的会话密钥"""
        return Fernet.generate_key()

    def encrypt_session_key(self, session_key):
        """使用RSA公钥加密会话密钥"""
        if not self.public_key:
            raise ValueError("公钥未加载")
        return self.public_key.encrypt(
            session_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

    def decrypt_session_key(self, encrypted_session_key):
        """使用RSA私钥解密会话密钥"""
        if not self.private_key:
            raise ValueError("私钥未加载")
        return self.private_key.decrypt(
            encrypted_session_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

    def create_secure_message(self, data):
        """创建加密且带签名的消息"""
        if not self.session_key:
            raise ValueError("No session key available")

        # 添加时间戳
        data["timestamp"] = int(time.time())
        
        # 使用会话密钥加密
        fernet = Fernet(self.session_key)
        data_bytes = json.dumps(data).encode()
        encrypted_data = fernet.encrypt(data_bytes)
        
        # 计算HMAC签名
        hmac_obj = hmac.new(self.hmac_key, encrypted_data, hashlib.sha256)
        signature = b64encode(hmac_obj.digest()).decode()
        
        return {
            "encrypted_data": encrypted_data.decode(),
            "signature": signature,
            "timestamp": data["timestamp"]
        }

    def decrypt_message(self, secure_message):
        """解密并验证消息"""
        if not self.session_key:
            raise ValueError("No session key available")

        # 验证签名
        if not self.verify_signature(secure_message["encrypted_data"], secure_message["signature"]):
            raise ValueError("Invalid signature")

        # 验证时间戳
        if not self.verify_timestamp(secure_message["timestamp"]):
            raise ValueError("Timestamp expired")

        # 解密数据
        fernet = Fernet(self.session_key)
        decrypted_data = fernet.decrypt(secure_message["encrypted_data"].encode())
        return json.loads(decrypted_data)

    def verify_signature(self, encrypted_data, signature):
        """验证消息签名"""
        hmac_obj = hmac.new(self.hmac_key, encrypted_data.encode(), hashlib.sha256)
        expected_signature = b64encode(hmac_obj.digest()).decode()
        return hmac.compare_digest(signature, expected_signature)

    def verify_timestamp(self, timestamp):
        """验证时间戳是否在有效期内"""
        current_time = int(time.time())
        return abs(current_time - timestamp) <= self.timestamp_validity
