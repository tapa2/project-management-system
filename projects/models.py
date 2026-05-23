from django.conf import settings
from django.db import models


class Project(models.Model):
    name = models.CharField(max_length=150, verbose_name='Назва')
    description = models.TextField(blank=True, verbose_name='Опис')
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_projects',
        verbose_name='Власник',
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='ProjectMembership',
        related_name='projects',
        verbose_name='Учасники',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Створено')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Оновлено')
    is_active = models.BooleanField(default=True, verbose_name='Активний')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Проєкт'
        verbose_name_plural = 'Проєкти'

    def __str__(self) -> str:
        return self.name


class ProjectMembership(models.Model):
    class Role(models.TextChoices):
        OWNER = 'owner', 'Власник'
        MANAGER = 'manager', 'Менеджер'
        MEMBER = 'member', 'Учасник'

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='memberships',
        verbose_name='Проєкт',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='memberships',
        verbose_name='Користувач',
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.MEMBER,
        verbose_name='Роль',
    )
    joined_at = models.DateTimeField(auto_now_add=True, verbose_name='Приєднався')

    class Meta:
        unique_together = ('project', 'user')
        ordering = ['-joined_at']
        verbose_name = 'Учасник проєкту'
        verbose_name_plural = 'Учасники проєктів'

    def __str__(self) -> str:
        return f'{self.user} — {self.project} ({self.get_role_display()})'
