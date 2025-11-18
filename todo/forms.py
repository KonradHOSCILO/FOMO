from django import forms
from django.utils import timezone

from .models import Task, TaskGroup


DATETIME_FORMAT = "%Y-%m-%dT%H:%M"


class DateTimeLocalInput(forms.DateTimeInput):
    input_type = "datetime-local"

    def __init__(self, **kwargs):
        kwargs.setdefault("format", DATETIME_FORMAT)
        super().__init__(**kwargs)


class ColorInput(forms.TextInput):
    input_type = "color"


class TaskForm(forms.ModelForm):
    due_date = forms.DateTimeField(
        required=False,
        widget=DateTimeLocalInput(
            attrs={"class": "input", "placeholder": "2025-12-31T18:30"},
        ),
    )

    class Meta:
        model = Task
        fields = [
            "title",
            "description",
            "due_date",
            "priority",
            "group",
            "repeat_frequency",
            "repeat_interval",
            "repeat_until",
            "accent_color",
            "icon",
            "theme_variant",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "input", "placeholder": "Np. Zetrzyj kurze"}),
            "description": forms.Textarea(
                attrs={"rows": 3, "class": "textarea", "placeholder": "Opis, checklisty..."}
            ),
            "priority": forms.Select(attrs={"class": "select"}),
            "group": forms.Select(attrs={"class": "select"}),
            "repeat_frequency": forms.Select(attrs={"class": "select"}),
            "repeat_interval": forms.NumberInput(attrs={"class": "input", "min": 1}),
            "repeat_until": forms.DateInput(attrs={"class": "input", "type": "date"}),
            "accent_color": ColorInput(attrs={"class": "color-input"}),
            "icon": forms.TextInput(attrs={"class": "input", "placeholder": "np. ph-sun-dim"}),
            "theme_variant": forms.Select(
                choices=[
                    ("base", "Domyślny"),
                    ("pastel", "Pastelowy"),
                    ("mono", "Monochromatyczny"),
                    ("vibrant", "Wyrazisty"),
                ],
                attrs={"class": "select"},
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.due_date:
            local_dt = timezone.localtime(self.instance.due_date)
            self.initial["due_date"] = local_dt.strftime(DATETIME_FORMAT)
        if "repeat_until" in self.fields and self.instance and self.instance.repeat_until:
            self.initial["repeat_until"] = self.instance.repeat_until.strftime("%Y-%m-%d")

    def clean_repeat_interval(self):
        interval = self.cleaned_data.get("repeat_interval") or 1
        if interval < 1:
            raise forms.ValidationError("Odstęp powtórzeń musi być większy od zera.")
        return interval

    def clean(self):
        cleaned = super().clean()
        frequency = cleaned.get("repeat_frequency")
        if frequency == Task.RepeatFrequency.NONE:
            cleaned["repeat_interval"] = 1
            cleaned["repeat_until"] = None
        return cleaned


class TaskGroupForm(forms.ModelForm):
    class Meta:
        model = TaskGroup
        fields = ["name", "color", "icon"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "input", "placeholder": "Np. Sprzątanie"}),
            "color": ColorInput(attrs={"class": "color-input"}),
            "icon": forms.TextInput(attrs={"class": "input", "placeholder": "ph-broom"}),
        }

