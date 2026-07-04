"""
安全相关工具
1. `get_password_hash`：注册时把密码加密存库
2. `verify_password`：登录时对比输入密码和库中哈希
3. `create_access_token`：通用生成 JWT
4. `decode_access_token`：解析并校验 JWT 是否合法有效
5. `create_token_for_user`：登录接口专用，组装好标准返回给前端
"""
from datetime import timedelta, datetime
from typing import Dict, Any, Optional

import bcrypt
from jose import jwt, JWTError

from config import settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证明文密码和数据库存储的哈希是否匹配"""
    # 明文密码、哈希密码转字节，调用bcrypt校验，返回True、False
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

def get_password_hash(password: str) -> str:
    """将原始明文密码加密，生成哈希字符串存入数据库"""
    # gensalt() 生成随机盐 hashpw加盐加密 decode转回字符串存储
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def create_access_token(
    data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
) -> str:
    """
    创建JWT Token
    :param data: 要编码近token的数据，必须包含user_id金额tenant_id
    :param expires_delta: 自定义过期时长
    :return: 加密后的JWT token字符串
    """
    # 拷贝一份传入的数据，避免修改原字典
    to_encode = data.copy()

    # 如果传入了自定义过期时间，使用自定义时间
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    # 没传使用配置文件默认的过期分钟数
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    # 向token载荷添加两个标准字段
    to_encode.update({
        "exp": expire, # token过期时间戳
        "iat": datetime.utcnow(), # token签发时间戳
    })

    # 使用密钥和指定算法加密生成token
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return encoded_jwt

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    解码JWT Token，校验签名、有效期
    :param token: 前端传过来的JWT、token字符串
    :return: 解码后的载荷字典：过期、篡改、密钥错误全部返回None
    """
    try:
        # 使用同一密钥和算法解密并校验token合法性
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return payload
    # 捕获所有JWT异常、过期、签名错误、格式错误等
    except JWTError:
        return None

def create_token_for_user(user_id: int, tenant_id: int, username: str) -> Dict[str, Any]:
    """
    为登录用户生成完整返回格式的令牌
    :param user_id:
    :param tenant_id:
    :param username:
    :return:
    """
    # 从配置读取默认过期时长
    expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    # 调用上层函数生成加密token，存入用户基础信息
    access_token = create_access_token(
        data={
            "user_id": user_id,
            "tenant_id": tenant_id,
            "username": username,
        },
        expires_delta = expires_delta
    )

    # 封装前端需要的标准返回结构
    return {
        "access_token": access_token, # 令牌字符串
        "token_type": "bearer", # 认证类型，前端请求头固定Bearer
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60, # 剩余有效期
    }