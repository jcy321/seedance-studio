import smtplib
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional

from app.core.config import settings


class EmailService:
    def __init__(self):
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_user = settings.smtp_user
        self.smtp_password = settings.smtp_pass
        self._verification_codes: Dict[str, Tuple[str, datetime]] = {}

    def generate_verification_code(self) -> str:
        return "".join(random.choices(string.digits, k=6))

    async def send_verification_code(self, email: str) -> str:
        code = self.generate_verification_code()
        expire_time = datetime.utcnow() + timedelta(minutes=10)
        self._verification_codes[email] = (code, expire_time)

        # 开发模式：在日志中打印验证码
        if settings.debug:
            print(f"[DEV] 验证码 for {email}: {code}")
            return code

        msg = MIMEMultipart()
        msg["From"] = self.smtp_user
        msg["To"] = email
        msg["Subject"] = "Seedance Studio - 邮箱验证码"

        body = f"""<div style="font-family: sans-serif; max-width: 480px; margin: 0 auto;">
<h2 style="color: #FF6B00;">Seedance Studio</h2>
<p>您的验证码是：</p>
<div style="font-size: 32px; font-weight: bold; color: #FF6B00; letter-spacing: 8px; text-align: center; padding: 20px; background: #f5f5f5; border-radius: 8px;">
{code}
</div>
<p style="color: #666;">验证码有效期为10分钟，请尽快完成验证。</p>
<p style="color: #999; font-size: 12px;">如果这不是您本人的操作，请忽略此邮件。</p>
</div>"""
        msg.attach(MIMEText(body, "html"))

        try:
            server = smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10)
            server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            server.send_message(msg)
            server.quit()
        except Exception as e:
            raise Exception(f"邮件发送失败: {e}")

        return code

    def verify_code(self, email: str, code: str) -> bool:
        # 开发模式：000000 万能验证码
        if settings.debug and code == "000000":
            return True

        record = self._verification_codes.get(email)
        if not record:
            return False

        saved_code, expire_time = record
        if datetime.utcnow() > expire_time:
            self._verification_codes.pop(email, None)
            return False

        if saved_code != code:
            return False

        self._verification_codes.pop(email, None)
        return True

    def cleanup_expired(self):
        now = datetime.utcnow()
        expired = [k for k, v in self._verification_codes.items() if v[1] < now]
        for k in expired:
            self._verification_codes.pop(k, None)
