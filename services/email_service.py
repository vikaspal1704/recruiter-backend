# services/email_service.py
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

SENDGRID_KEY = os.getenv("SENDGRID_API_KEY")

def send_email(to_email: str, subject: str, content: str):
    message = Mail(
        from_email="noreply@yourdomain.com",
        to_emails=to_email,
        subject=subject,
        html_content=content
    )
    sg = SendGridAPIClient(SENDGRID_KEY)
    resp = sg.send(message)
    return resp.status_code, resp.body
