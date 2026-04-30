import asyncio
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings


def _send_sync(to_email: str, subject: str, html: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.email_user
    msg["To"] = to_email
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP(settings.email_host, settings.email_port) as smtp:
        smtp.starttls()
        smtp.login(settings.email_user, settings.email_password)
        smtp.sendmail(settings.email_user, to_email, msg.as_string())


async def send_trip_invitation(
    to_email: str,
    trip_name: str,
    inviter_email: str,
    token: str,
) -> None:
    accept_url = (
        f"{settings.app_base_url}/trips/invitations/accept?token={token}"
    )

    html = f"""
    <div style="font-family:sans-serif;max-width:480px;margin:0 auto">
      <h2 style="color:#f97316">You're invited to a trip!</h2>
      <p><strong>{inviter_email}</strong> has invited you to join
         <strong>{trip_name}</strong> on AI Travel Planner.</p>
      <a href="{accept_url}"
         style="display:inline-block;margin-top:16px;padding:12px 24px;
                background:#f97316;color:#fff;border-radius:8px;
                text-decoration:none;font-weight:600">
        Accept Invitation
      </a>
      <p style="margin-top:24px;color:#71717a;font-size:13px">
        This link expires in 7 days. If you don't have an account yet,
        you'll be prompted to create one first.
      </p>
    </div>
    """

    subject = f"You've been invited to '{trip_name}'"

    if not settings.email_user or settings.email_user == "your@gmail.com":
        print(f"\n[DEV] Invitation link for {to_email}: {accept_url}\n")
        return

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _send_sync, to_email, subject, html)
