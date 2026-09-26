import os
import uuid
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


def book_file_path(instance, filename):
    """Генерирует уникальный путь для файла книги: media/books/files/uuid.ext"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('books/files/', filename)


def book_cover_path(instance, filename):
    """Генерирует уникальный путь для обложки книги: media/books/covers/uuid.ext"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('books/covers/', filename)


class Author(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='author_profile',
        verbose_name='Аккаунт пользователя'
    )
    first_name = models.CharField(max_length=100, verbose_name='Имя')
    last_name = models.CharField(max_length=100, verbose_name='Фамилия')
    bio = models.TextField(blank=True, verbose_name='Биография')
    photo = models.ImageField(upload_to='authors/', blank=True, null=True, verbose_name='Фото')

    class Meta:
        verbose_name = 'Автор'
        verbose_name_plural = 'Авторы'

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='Название')
    slug = models.SlugField(max_length=100, unique=True, verbose_name='URL Slug')

    class Meta:
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'

    def __str__(self):
        return self.name


class Book(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Черновик'
        PENDING = 'pending', 'На модерации'
        PUBLISHED = 'published', 'Опубликовано'
        REJECTED = 'rejected', 'Отклонено'

    class Format(models.TextChoices):
        PDF = 'pdf', 'PDF'
        EPUB = 'epub', 'EPUB'
        FB2 = 'fb2', 'FB2'

    title = models.CharField(max_length=255, verbose_name='Название')
    slug = models.SlugField(max_length=255, unique=True, verbose_name='URL Slug')
    description = models.TextField(verbose_name='Описание')
    cover = models.ImageField(upload_to=book_cover_path, blank=True, null=True, verbose_name='Обложка')
    file = models.FileField(upload_to=book_file_path, verbose_name='Файл книги')
    file_format = models.CharField(max_length=10, choices=Format.choices, verbose_name='Формат файла')
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name='Статус'
    )

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='uploaded_books',
        verbose_name='Кем загружено'
    )
    authors = models.ManyToManyField(Author, related_name='books', verbose_name='Авторы')
    genres = models.ManyToManyField(Genre, related_name='books', verbose_name='Жанры')

    publication_year = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='Год издания')
    views_count = models.PositiveIntegerField(default=0, verbose_name='Просмотры')
    downloads_count = models.PositiveIntegerField(default=0, verbose_name='Скачивания')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')

    class Meta:
        verbose_name = 'Книга'
        verbose_name_plural = 'Книги'
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class FavoriteBook(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь'
    )
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name='favorited_by',
        verbose_name='Книга'
    )
    added_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')

    class Meta:
        verbose_name = 'Избранная книга'
        verbose_name_plural = 'Избранные книги'
        unique_together = ('user', 'book')

    def __str__(self):
        return f"{self.user.username} -> {self.book.title}"


class ReadingProgress(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reading_progress',
        verbose_name='Пользователь'
    )
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name='readers_progress',
        verbose_name='Книга'
    )
    last_page = models.PositiveIntegerField(default=1, verbose_name='Последняя страница')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Прогресс чтения'
        verbose_name_plural = 'Прогресс чтения'
        unique_together = ('user', 'book')

    def __str__(self):
        return f"{self.user.username} - {self.book.title} (Стр. {self.last_page})"


class Review(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Пользователь'
    )
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Книга'
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='Оценка (1-5)'
    )
    text = models.TextField(verbose_name='Текст отзыва')
    is_approved = models.BooleanField(default=False, verbose_name='Одобрен модератором')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ['-created_at']

    def __str__(self):
        return f"Отзыв от {self.user.username} на {self.book.title}"