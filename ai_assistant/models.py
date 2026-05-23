from django.conf import settings
from django.db import models


class AISuggestion(models.Model):
    class Kind(models.TextChoices):
        DESCRIPTION = 'description', 'Опис задачі'
        CATEGORIZATION = 'categorization', 'Категоризація'
        CHAT = 'chat', 'Чат-помічник'
        OTHER = 'other', 'Інше'

    task = models.ForeignKey(
        'tasks.Task',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ai_suggestions',
        verbose_name='Задача',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ai_suggestions',
        verbose_name='Користувач',
    )
    kind = models.CharField(
        max_length=20,
        choices=Kind.choices,
        default=Kind.OTHER,
        verbose_name='Тип',
    )
    prompt = models.TextField(verbose_name='Запит')
    response = models.TextField(blank=True, verbose_name='Відповідь')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Створено')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'AI-підказка'
        verbose_name_plural = 'AI-підказки'

    def __str__(self) -> str:
        return f'{self.get_kind_display()} — {self.user} ({self.created_at:%Y-%m-%d %H:%M})'
