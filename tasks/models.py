from django.conf import settings
from django.db import models


class Label(models.Model):
    name = models.CharField(max_length=40, unique=True, verbose_name='Назва')
    color = models.CharField(
        max_length=7,
        default='#6c757d',
        help_text='HEX-колір, напр. #ff5733',
        verbose_name='Колір',
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Мітка'
        verbose_name_plural = 'Мітки'

    def __str__(self) -> str:
        return self.name


class Task(models.Model):
    class Status(models.TextChoices):
        TODO = 'todo', 'До виконання'
        IN_PROGRESS = 'in_progress', 'В роботі'
        REVIEW = 'review', 'На перевірці'
        DONE = 'done', 'Готово'

    class Priority(models.TextChoices):
        LOW = 'low', 'Низький'
        MEDIUM = 'medium', 'Середній'
        HIGH = 'high', 'Високий'
        CRITICAL = 'critical', 'Критичний'

    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='tasks',
        verbose_name='Проєкт',
    )
    title = models.CharField(max_length=200, verbose_name='Заголовок')
    description = models.TextField(blank=True, verbose_name='Опис')
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tasks',
        verbose_name='Виконавець',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_tasks',
        verbose_name='Автор',
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.TODO,
        verbose_name='Статус',
    )
    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.MEDIUM,
        verbose_name='Пріоритет',
    )
    deadline = models.DateTimeField(null=True, blank=True, verbose_name='Дедлайн')
    labels = models.ManyToManyField(Label, blank=True, related_name='tasks', verbose_name='Мітки')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Створено')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Оновлено')

    class Meta:
        ordering = ['status', 'order', '-created_at']
        verbose_name = 'Задача'
        verbose_name_plural = 'Задачі'

    def __str__(self) -> str:
        return self.title


class Comment(models.Model):
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Задача',
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор',
    )
    text = models.TextField(verbose_name='Текст')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Створено')

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Коментар'
        verbose_name_plural = 'Коментарі'

    def __str__(self) -> str:
        return f'{self.author} → {self.task} ({self.created_at:%Y-%m-%d %H:%M})'


class Attachment(models.Model):
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name='Задача',
    )
    file = models.FileField(upload_to='attachments/%Y/%m/', verbose_name='Файл')
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_attachments',
        verbose_name='Завантажив',
    )
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='Завантажено')

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Вкладення'
        verbose_name_plural = 'Вкладення'

    def __str__(self) -> str:
        return f'{self.file.name} ({self.task})'
