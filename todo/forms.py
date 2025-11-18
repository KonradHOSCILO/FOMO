from django import forms

from .models import Task, TaskGroup


class ColorInput(forms.TextInput):
    input_type = "color"


class TaskForm(forms.ModelForm):
    """Simple task form with only essential fields."""
    
    class Meta:
        model = Task
        fields = ["title", "description", "group", "repeat_frequency"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "input", "placeholder": "Nazwa zadania"}),
            "description": forms.Textarea(attrs={"class": "input", "placeholder": "Opis zadania (opcjonalnie)", "rows": 2}),
            "group": forms.Select(attrs={"class": "select"}),
            "repeat_frequency": forms.Select(attrs={"class": "select"}),
        }


class TaskGroupForm(forms.ModelForm):
    class Meta:
        model = TaskGroup
        fields = ["name", "color"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "input", "placeholder": "Np. Sprzątanie"}),
            "color": ColorInput(attrs={"class": "color-input"}),
        }

