from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from .models import Task, TaskGroup


class TaskModelTests(TestCase):
    def setUp(self):
        self.group_work = TaskGroup.objects.create(name="Praca", color="#ff8800")
        self.group_home = TaskGroup.objects.create(name="Dom", color="#00ffaa")

    def test_priority_sorting(self):
        low = Task.objects.create(title="Niskie", priority=Task.Priority.LOW)
        high = Task.objects.create(title="Wysokie", priority=Task.Priority.HIGH)
        medium = Task.objects.create(title="Średnie", priority=Task.Priority.MEDIUM)

        ordered = list(Task.objects.sorted("priority"))
        self.assertEqual([task.title for task in ordered], ["Wysokie", "Średnie", "Niskie"])

        # ensure queryset can be filtered by group
        low.group = self.group_work
        low.save()
        ordered_group = list(Task.objects.sorted("priority", group_id=self.group_work.id))
        self.assertEqual(ordered_group[0], low)

    def test_repeat_creates_next_occurrence(self):
        due = timezone.now()
        task = Task.objects.create(
            title="Powtórka",
            due_date=due,
            repeat_frequency=Task.RepeatFrequency.DAILY,
            repeat_interval=2,
            group=self.group_work,
        )
        next_due = task.calculate_next_due_date()
        self.assertAlmostEqual(next_due.timestamp(), (due + timedelta(days=2)).timestamp(), delta=1)

        new_task = task.spawn_next_occurrence()
        self.assertIsNotNone(new_task)
        self.assertEqual(new_task.group, task.group)
        self.assertEqual(new_task.priority, task.priority)
        self.assertFalse(new_task.is_completed)
        self.assertEqual(new_task.repeat_frequency, task.repeat_frequency)

    def test_toggle_completion_triggers_repeat(self):
        task = Task.objects.create(
            title="Zadanie cykliczne",
            repeat_frequency=Task.RepeatFrequency.WEEKLY,
            due_date=timezone.now(),
        )
        task.toggle_completion()
        self.assertTrue(task.is_completed)
        self.assertEqual(Task.objects.count(), 2)

    def test_move_between_groups(self):
        task = Task.objects.create(title="Przenieś mnie", group=self.group_home, position=1)
        task.move_to(self.group_work, position=5)
        task.refresh_from_db()
        self.assertEqual(task.group, self.group_work)
        self.assertEqual(task.position, 5)


class TaskGroupTests(TestCase):
    def test_slug_is_generated(self):
        group = TaskGroup.objects.create(name="Porządki domowe", color="#ffffff")
        self.assertTrue(group.slug.startswith("porzadki-domowe"))
