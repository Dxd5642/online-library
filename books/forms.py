from django import forms
from django.utils.text import slugify
import uuid
from .models import Book, Genre, Author, Review


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = [
            'title',
            'description',
            'cover',
            'file',
            'file_format',
            'publication_year',
            'genres',
            'authors',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Название книги'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Описание'
            }),
            'cover': forms.FileInput(attrs={'class': 'form-control'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'file_format': forms.Select(attrs={'class': 'form-select'}),
            'publication_year': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Например: 2024'
            }),
            'genres': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'size': 5
            }),
            'authors': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'size': 5
            }),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        # Соавторы необязательны
        self.fields['authors'].required = False

        # Не показываем самого текущего автора в списке соавторов
        if user and hasattr(user, 'author_profile'):
            self.fields['authors'].queryset = Author.objects.exclude(
                pk=user.author_profile.pk
            )

    def save(self, commit=True, user=None):
        book = super().save(commit=False)

        # Автогенерация slug
        if not book.slug:
            base_slug = slugify(book.title)

            if not base_slug:
                base_slug = f"book-{uuid.uuid4().hex[:8]}"

            book.slug = f"{base_slug}-{uuid.uuid4().hex[:6]}"

        if user:
            book.uploaded_by = user
            book.status = Book.Status.PENDING

        if commit:
            book.save()
            self.save_m2m()

        return book



class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'text']
        widgets = {
            'rating': forms.Select(
                choices=[(i, f'★ {i}' if i == 1 else f'★ {i}') for i in range(5, 0, -1)],
                attrs={'class': 'form-select'}
            ),
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Поделитесь впечатлениями о прочитанной книге...'
            }),
        }
        labels = {
            'rating': 'Ваша оценка',
            'text': 'Текст отзыва',
        }