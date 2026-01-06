from django import forms
from django.contrib.auth import authenticate
from todo.models import Task, TaskGroup, User


class TaskCreateForm(forms.Form):
    title = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={"class": "input", "placeholder": "Nowe zadanie..."})
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "input", "placeholder": "Opis zadania (opcjonalnie)", "rows": 2})
    )
    group = forms.ChoiceField(
        choices=Task.Group.choices,
        widget=forms.Select(attrs={"class": "select"})
    )
    file = forms.FileField(required=False)


class RegisterForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={"class": "input"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "input"}))

    def clean_email(self):
        email = self.cleaned_data["email"].lower().strip()
        if User.objects.filter(mail=email).exists():
            raise forms.ValidationError("Taki email już istnieje.")
        return email

    def save(self) -> User:
        email = self.cleaned_data["email"].lower().strip()
        password = self.cleaned_data["password"]
        return User.objects.create_user(email=email, password=password)


class LoginForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={"class": "input"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "input"}))

    def clean(self):
        cleaned = super().clean()
        email = cleaned.get("email")
        password = cleaned.get("password")
        if not email or not password:
            return cleaned

        user = authenticate(username=email, password=password)
        if not user:
            raise forms.ValidationError("Nieprawidłowy email lub hasło.")
        cleaned["user"] = user
        return cleaned
