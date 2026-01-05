import smtplib
from email.message import EmailMessage

SMTP_HOST = "ssl0.ovh.net"
SMTP_PORT = 465

SMTP_USER = "no-reply@fomo.com.pl"
SMTP_PASS = "&yYm7<Pr5XTS"

TO_EMAIL = "konrad.hamiloo@gmail.com"

msg = EmailMessage()
msg["Subject"] = "FOMO – test maila (Zimbra OVH)"
msg["From"] = SMTP_USER
msg["To"] = TO_EMAIL
msg.set_content(
    "To jest test wysyłki maila z chmurowej usługi Zimbra (OVH)."
)

with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as smtp:
    smtp.login(SMTP_USER, SMTP_PASS)
    smtp.send_message(msg)

print("✅ Mail wysłany poprawnie")
