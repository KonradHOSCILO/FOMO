import os
import smtplib
from email.message import EmailMessage

SMTP_HOST = "smtp.mail.ovh.net"
SMTP_PORT = 587
USERNAME = "no-reply@fomo-projekt.tech"
PASSWORD = "&yYm7<Pr5XTS"

TO_ADDR = "konrad.hamiloo@gmail.com"

msg = EmailMessage()
msg["From"] = USERNAME
msg["To"] = TO_ADDR
msg["Subject"] = "Test SMTP (OVH) — fomo-projekt.tech"
msg.set_content("Cześć! To jest testowy mail wysłany przez SMTP OVH (587/STARTTLS).")

with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as server:
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(USERNAME, PASSWORD)
    server.send_message(msg)

print("Wysłano mail testowy")
