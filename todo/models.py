from datetime import timedelta

from dateutil.relativedelta import relativedelta
from django.db import models
from django.db.models import F, Max, Value
from django.utils import timezone
from django.utils.text import slugify


PRIORITY_WEIGHTS = {
    "high": 3,
    "medium": 2,
    "low": 1,
}


class TaskGroup(models.Model):
    """
    Kolekcja zadań reprezentująca kategorię lub kontekst (np. Sprzątanie).
    """

    name = models.CharField(max_length=80, unique=True)
    color = models.CharField(max_length=20, default="#5c6b7a")
    icon = models.CharField(
        max_length=60,
        default="ph-list-checks",
        help_text="Nazwa ikony (np. z biblioteki Phosphor Icons).",
    )
    order = models.PositiveIntegerField(default=0)
    slug = models.SlugField(max_length=80, unique=True, blank=True)

    class Meta:
        ordering = ["order", "name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name) or "group"
            candidate = base
            suffix = 1
            while TaskGroup.objects.exclude(pk=self.pk).filter(slug=candidate).exists():
                suffix += 1
                candidate = f"{base}-{suffix}"
            self.slug = candidate

        if self.order == 0:
            max_order = TaskGroup.objects.exclude(pk=self.pk).aggregate(max_=Max("order"))["max_"] or 0
            self.order = max_order + 1

        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name


class TaskQuerySet(models.QuerySet):
    def sorted(self, criterion: str = "priority"):
        criterion = (criterion or "priority").lower()
        if criterion == "date":
            return self.order_by(
                F("due_date").asc(nulls_last=True),
                F("priority_weight").desc(),
                "group__order",
                "created_at",
            )
        if criterion == "group":
            return self.order_by("group__order", "group__name", "-priority_weight", "position", "-created_at")
        return self.order_by("-priority_weight", "position", "group__order", "-created_at")

    def for_group(self, group_id: int | None):
        if not group_id:
            return self
        return self.filter(group_id=group_id)


class TaskManager(models.Manager):
    def get_queryset(self):
        qs = TaskQuerySet(self.model, using=self._db)
        return qs.select_related("group").annotate(
            priority_weight=models.Case(
                models.When(priority="high", then=Value(PRIORITY_WEIGHTS["high"])),
                models.When(priority="medium", then=Value(PRIORITY_WEIGHTS["medium"])),
                default=Value(PRIORITY_WEIGHTS["low"]),
                output_field=models.IntegerField(),
            )
        )

    def sorted(self, criterion="priority", group_id=None):
        qs = self.get_queryset()
        if group_id:
            qs = qs.filter(group_id=group_id)
        return qs.sorted(criterion)


class Task(models.Model):
    """
    Pojedyncze zadanie w aplikacji FOMO.
    """

    class Priority(models.TextChoices):
        LOW = "low", "Niski"
        MEDIUM = "medium", "Średni"
        HIGH = "high", "Wysoki"

    class RepeatFrequency(models.TextChoices):
        NONE = "none", "Brak"
        DAILY = "daily", "Codziennie"
        WEEKLY = "weekly", "Co tydzień"
        MONTHLY = "monthly", "Co miesiąc"

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    group = models.ForeignKey(TaskGroup, null=True, blank=True, on_delete=models.SET_NULL, related_name="tasks")
    priority = models.CharField(max_length=16, choices=Priority.choices, default=Priority.MEDIUM)
    accent_color = models.CharField(max_length=20, default="#6c7ae0")
    icon = models.CharField(max_length=60, default="ph-check-circle")
    theme_variant = models.CharField(
        max_length=20,
        default="base",
        help_text="Wariant stylistyczny kafelka (np. pastel, mono, vibrant).",
    )
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    repeat_frequency = models.CharField(max_length=16, choices=RepeatFrequency.choices, default=RepeatFrequency.NONE)
    repeat_interval = models.PositiveIntegerField(default=1)
    repeat_until = models.DateField(null=True, blank=True)
    position = models.PositiveIntegerField(default=0)

    objects = TaskManager()

    class Meta:
        ordering = ["is_completed", "-priority", "position", "-created_at"]

    def __str__(self) -> str:
        return self.title

    # ----- Ordering helpers -------------------------------------------------
    def _assign_position_if_needed(self):
        if self.position:
            return
        last_position = (
            Task.objects.filter(group=self.group)
            .exclude(pk=self.pk)
            .aggregate(max_pos=Max("position"))["max_pos"]
            or 0
        )
        self.position = last_position + 1

    # ----- Repeating logic --------------------------------------------------
    @property
    def should_repeat(self) -> bool:
        return self.repeat_frequency != self.RepeatFrequency.NONE

    def calculate_next_due_date(self):
        if not self.should_repeat:
            return None

        base = self.due_date or timezone.now()
        if self.repeat_frequency == self.RepeatFrequency.DAILY:
            candidate = base + timedelta(days=self.repeat_interval)
        elif self.repeat_frequency == self.RepeatFrequency.WEEKLY:
            candidate = base + timedelta(weeks=self.repeat_interval)
        elif self.repeat_frequency == self.RepeatFrequency.MONTHLY:
            candidate = base + relativedelta(months=self.repeat_interval)
        else:
            return None

        if self.repeat_until and candidate.date() > self.repeat_until:
            return None
        return candidate

    def spawn_next_occurrence(self):
        next_due = self.calculate_next_due_date()
        if not next_due:
            return None

        return Task.objects.create(
            title=self.title,
            description=self.description,
            group=self.group,
            priority=self.priority,
            accent_color=self.accent_color,
            icon=self.icon,
            theme_variant=self.theme_variant,
            due_date=next_due,
            repeat_frequency=self.repeat_frequency,
            repeat_interval=self.repeat_interval,
            repeat_until=self.repeat_until,
        )

    def toggle_completion(self):
        self.is_completed = not self.is_completed
        self.completed_at = timezone.now() if self.is_completed else None
        self.save(update_fields=["is_completed", "completed_at"])
        if self.is_completed and self.should_repeat:
            self.spawn_next_occurrence()

    def move_to(self, group: TaskGroup | None, position: int | None = None):
        self.group = group
        if not position or position < 1:
            self.position = 0
        else:
            self.position = position
        self.save()

    # ----- CRUD overrides ---------------------------------------------------
    def save(self, *args, **kwargs):
        self._assign_position_if_needed()
        super().save(*args, **kwargs)
