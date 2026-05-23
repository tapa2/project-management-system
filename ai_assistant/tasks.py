from celery import shared_task

from .models import AISuggestion
from .services import generate_task_description


@shared_task(bind=True, name='ai_assistant.generate_task_description')
def generate_task_description_task(self, suggestion_id: int) -> int:
    """Згенерувати опис для AISuggestion та зберегти у `response`."""
    suggestion = AISuggestion.objects.get(pk=suggestion_id)
    try:
        suggestion.response = generate_task_description(suggestion.prompt)
    except Exception as exc:
        suggestion.response = f'Помилка генерації: {exc}'
        suggestion.save(update_fields=['response'])
        raise
    suggestion.save(update_fields=['response'])
    return suggestion.pk
