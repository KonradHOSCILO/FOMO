import os
import django


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fomo.settings')
django.setup()


from django.core.mail import send_mail


try:
    send_mail(
        subject="Test DirectMail z test_mail.py",
        message="OK",
        from_email=None,
        recipient_list=["konrad.hamiloo@gmail.com"],
    )
    print("✔️ Mail wysłany!")
except Exception as e:
    print("Błąd podczas wysyłania maila:")
    print(e)
