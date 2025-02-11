from django.contrib.auth.models import AbstractUser
from django.core.validators import EmailValidator, RegexValidator
from django.db import models
from django.forms import ValidationError

from foodgram.constants import (
    EMAIL_LENGTH,
    FIRST_NAME_LENGTH,
    LAST_NAME_LENGTH,
    USERNAME_LENGTH
)


class User(AbstractUser):
    """Модель пользователя."""

    username = models.CharField(
        max_length=USERNAME_LENGTH,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[\w.@+-]+\Z',
                message=('Имя пользователя может содержать '
                         'только латинские буквы, цифры и символы: @ . + - _'
                         )
            )
        ],
        verbose_name='Имя пользователя',
    )

    first_name = models.CharField(
        max_length=FIRST_NAME_LENGTH,
        verbose_name='Имя'
    )

    last_name = models.CharField(
        max_length=LAST_NAME_LENGTH,
        verbose_name='Фамилия'
    )

    email = models.EmailField(
        max_length=EMAIL_LENGTH,
        unique=True,
        validators=[EmailValidator()],
        verbose_name='Email'
    )

    avatar = models.ImageField(
        null=True,
        upload_to='users/avatars/',
        default=None,
        verbose_name='Аватар'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = (
        'username',
        'first_name',
        'last_name',
        'password'
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username


class Subscription(models.Model):
    """Модель подписки."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscription',
        verbose_name='Пользователь'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name='Автор'
    )

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_user_author'
            ),
        )
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def save(self, *args, **kwargs):
        if self.user == self.author:
            raise ValidationError("Нельзя подписаться на самого себя.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.user.username} подписан(а) на {self.author.username}'
