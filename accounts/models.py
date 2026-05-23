from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        verbose_name='Аватар',
    )
    position = models.CharField(
        max_length=120,
        blank=True,
        verbose_name='Посада',
    )
    bio = models.TextField(
        blank=True,
        verbose_name='Про себе',
    )

    class Meta:
        verbose_name = 'Користувач'
        verbose_name_plural = 'Користувачі'

    def __str__(self) -> str:
        return self.get_full_name() or self.username
