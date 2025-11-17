import os
import django

# 1. Ustawienie konfiguracji Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fomo.settings')
django.setup()

# 2. Import wysyłki maila
from django.core.mail import send_mail

# 3. Test
try:
    send_mail(
        subject="Test DirectMail z test_mail.py",
        message="Jeśli widzisz tego maila – wszystko działa! 🚀",
        from_email=None,  # użyje DEFAULT_FROM_EMAIL
        recipient_list=["konrad.hamiloo@gmail.com"],
    )
    print("✔️ Mail wysłany!")
except Exception as e:
    print("❌ Błąd podczas wysyłania maila:")
    print(e)
