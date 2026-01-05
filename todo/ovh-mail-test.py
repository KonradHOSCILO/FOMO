import socket
import smtplib
from email.message import EmailMessage

SMTP_HOST = "ssl0.ovh.net"
SMTP_PORT = 465

SMTP_USER = "no-reply@fomo-projekt.tech"
SMTP_PASS = "&yYm7<Pr5XTS"

TO_EMAIL = "konrad.hamiloo@gmail.com"

socket.setdefaulttimeout(15)

print("1) Tworzę wiadomość")
msg = EmailMessage()
msg["Subject"] = "FOMO – test maila (Zimbra OVH)"
msg["From"] = SMTP_USER
msg["To"] = TO_EMAIL
msg.set_content("Test wysyłki maila z OVH Zimbra.")

print(f"2) Łączę się z {SMTP_HOST}:{SMTP_PORT}")
with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=15) as smtp:
    smtp.set_debuglevel(1)   # <<< KLUCZOWE
    print("3) Logowanie SMTP")
    smtp.login(SMTP_USER, SMTP_PASS)
    print("4) Wysyłam maila")
    smtp.send_message(msg)

print("✅ Mail wysłany poprawnie")
