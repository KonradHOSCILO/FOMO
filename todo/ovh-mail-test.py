import os
import socket
import smtplib
from email.message import EmailMessage

SMTP_USER = os.getenv("SMTP_USER", "no-reply@fomo-projekt.tech")
SMTP_PASS = os.getenv("SMTP_PASS", "&yYm7<Pr5XTS")
TO_EMAIL  = os.getenv("TO_EMAIL", "konrad.hamiloo@gmail.com")

# 1) SSL 465
SMTP_HOST_SSL = os.getenv("SMTP_HOST_SSL", "ssl0.ovh.net")
SMTP_PORT_SSL = int(os.getenv("SMTP_PORT_SSL", "465"))

# 2) STARTTLS 587
SMTP_HOST_TLS = os.getenv("SMTP_HOST_TLS", "smtp.mail.ovh.net")
SMTP_PORT_TLS = int(os.getenv("SMTP_PORT_TLS", "587"))

TIMEOUT = int(os.getenv("SMTP_TIMEOUT", "20"))

msg = EmailMessage()
msg["Subject"] = "FOMO – test maila (OVH)"
msg["From"] = SMTP_USER
msg["To"] = TO_EMAIL
msg.set_content("Test wysyłki maila z OVH (serwer).")

def send_ssl():
    print(f"Łączę SSL: {SMTP_HOST_SSL}:{SMTP_PORT_SSL} (timeout={TIMEOUT}s)")
    with smtplib.SMTP_SSL(SMTP_HOST_SSL, SMTP_PORT_SSL, timeout=TIMEOUT) as smtp:
        smtp.set_debuglevel(1)
        smtp.login(SMTP_USER, SMTP_PASS)
        smtp.send_message(msg)

def send_starttls():
    print(f"Łączę STARTTLS: {SMTP_HOST_TLS}:{SMTP_PORT_TLS} (timeout={TIMEOUT}s)")
    with smtplib.SMTP(SMTP_HOST_TLS, SMTP_PORT_TLS, timeout=TIMEOUT) as smtp:
        smtp.set_debuglevel(1)
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(SMTP_USER, SMTP_PASS)
        smtp.send_message(msg)

try:
    send_ssl()
    print("✅ Wysłano przez SSL 465")
except (socket.timeout, TimeoutError, smtplib.SMTPConnectError) as e:
    print(f"⚠️ SSL 465 nie działa: {repr(e)}")
    print("➡️ Próbuję 587 STARTTLS...")
    send_starttls()
    print("✅ Wysłano przez STARTTLS 587")
except smtplib.SMTPAuthenticationError as e:
    print("❌ Błąd logowania SMTP (hasło/login).")
    raise
