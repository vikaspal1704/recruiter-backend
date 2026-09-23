# services/email_service.py
import os

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


def send_email(to_email: str, subject: str, content: str):
    api_key = os.getenv("SENDGRID_API_KEY")
    from_email = os.getenv("SENDGRID_FROM_EMAIL")
    if not (api_key and from_email):
        raise RuntimeError("Missing SENDGRID_API_KEY or SENDGRID_FROM_EMAIL in environment")

    message = Mail(
        from_email=from_email,
        to_emails=to_email,
        subject=subject,
        html_content=content
    )
    sg = SendGridAPIClient(api_key)
    resp = sg.send(message)
    return resp.status_code, resp.body
