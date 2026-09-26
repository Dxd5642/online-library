from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        READER = 'reader', 'Читатель'
        AUTHOR = 'author', 'Автор'
        MODERATOR = 'moderator', 'Модератор'
        ADMIN = 'admin', 'Администратор'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.READER,
        verbose_name='Роль'
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        verbose_name='Аватар'
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_author(self):
        return self.role == self.Role.AUTHOR

    @property
    def is_moderator(self):
        return (
            self.role in [self.Role.MODERATOR, self.Role.ADMIN] 
            or self.is_staff 
            or self.is_superuser
        )