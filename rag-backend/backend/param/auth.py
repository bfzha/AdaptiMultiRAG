from pydantic import BaseModel, Field, field_validator


class LoginRequest(BaseModel):
    """登录请求参数"""

    email: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email(cls, email: str) -> str:
        """执行轻量邮箱校验，避免额外引入 email-validator 依赖。"""
        email = email.strip()
        local_part, separator, domain = email.rpartition("@")
        if not separator or not local_part or "." not in domain:
            raise ValueError("请输入有效的邮箱地址")
        return email


class RegisterRequest(BaseModel):
    """注册请求参数"""
    username: str
    password: str
    email: str