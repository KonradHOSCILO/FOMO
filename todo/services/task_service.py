from django.db import transaction
from django.utils import timezone

from todo.models import Task, TaskGroup, Attachment
from todo.services.oss import upload_fileobj


@transaction.atomic
def create_task_with_optional_attachment(
    *,
    user,
    title: str,
    description: str = "",
    group: str,
    upload=None,
):
    task = Task.objects.create(
        user=user,
        title=title,
        description=description or "",
        group=group,
        status=Task.Status.TODO,
        created_at=timezone.now(),
        remind_at=None,
    )

    if upload:
        object_key = f"uploads/user_{user.id}/task_{task.id}/{upload.name}"
        file_url = upload_fileobj(upload, object_key=object_key)
        Attachment.objects.create(
            task=task,
            filename=upload.name,
            object_key=object_key,
            file_url=file_url,
            created_at=timezone.now(),
        )

    return task
