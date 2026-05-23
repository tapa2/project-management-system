import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET, require_POST

from .models import AISuggestion
from .tasks import generate_task_description_task


@login_required
@require_POST
def request_description(request):
    """Запустити Celery-таск генерації опису задачі за заголовком.

    Body: {"title": "...", "task_id": optional int}
    """
    try:
        payload = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'invalid json'}, status=400)

    title = (payload.get('title') or '').strip()
    if not title:
        return JsonResponse({'error': 'title is required'}, status=400)

    suggestion = AISuggestion.objects.create(
        user=request.user,
        kind=AISuggestion.Kind.DESCRIPTION,
        prompt=title,
        response='',
        task_id=payload.get('task_id') or None,
    )

    generate_task_description_task.delay(suggestion.pk)

    return JsonResponse({
        'suggestion_id': suggestion.pk,
        'status': 'pending',
    })


@login_required
@require_GET
def suggestion_status(request, pk: int):
    """Polling endpoint: повертає поточний стан AISuggestion."""
    suggestion = get_object_or_404(AISuggestion, pk=pk, user=request.user)
    return JsonResponse({
        'suggestion_id': suggestion.pk,
        'status': 'ready' if suggestion.response else 'pending',
        'response': suggestion.response,
    })
