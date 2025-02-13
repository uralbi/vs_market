import aiosmtplib, os
from email.message import EmailMessage
from app.infra.celery_fld.celery_config import celery_app
import asyncio, ssl
from dotenv import load_dotenv
load_dotenv()

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = os.getenv("SMTP_PORT")
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={"max_retries": 5, "countdown": 60})
def send_verification_email(self, to_email: str, verification_link: str):
    """Send an HTML email with a verification link asynchronously."""
    
    message = EmailMessage()
    message["From"] = SMTP_USERNAME
    message["To"] = to_email
    message["Subject"] = "Verify Your Account"

    # Plain text fallback
    message.set_content(f"Click the link to verify your account: {verification_link}")

    # HTML version of the email
    html_content = f"""
    <html>
        <body>
            <h2>Welcome to Our Platform!</h2>
            <p>Click the link below to verify your email:</p>
            <a href="{verification_link}" style="display:inline-block;padding:10px 20px;color:#fff;background:#007bff;text-decoration:none;border-radius:5px;">Verify Email</a>
        </body>
    </html>
    """
    message.add_alternative(html_content, subtype="html")

    async def send_email():
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        try:
            await aiosmtplib.send(
                message,
                hostname=SMTP_SERVER,
                port=SMTP_PORT,
                username=SMTP_USERNAME,
                password=SMTP_PASSWORD,
                use_tls=True,
                tls_context=context,
            )
        except Exception as e:
            raise self.retry(exc=e)  # ✅ Retries on failure
    asyncio.run(send_email())
    
    print('Verification email sent to:', to_email)
