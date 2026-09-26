from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth import get_user_model
from .models import User
from books.models import Author

User = get_user_model()

class UserRegisterForm(UserCreationForm):
    ROLE_CHOICES = [
        (User.Role.READER, 'Читатель (просмотр, скачивание, отзывы)'),
        (User.Role.AUTHOR, 'Автор (загрузка и публикация книг)'),
    ]

    email = forms.EmailField(
        required=True,
        label='Электронная почта',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@example.com'})
    )
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        initial=User.Role.READER,
        widget=forms.RadioSelect,
        label='Выберите роль'
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'role')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = self.cleaned_data['role']
        
        if commit:
            user.save()
            # Если выбран Автор — автоматически создаем профиль автора
            if user.role == User.Role.AUTHOR:
                Author.objects.get_or_create(
                    user=user,
                    defaults={
                        'first_name': user.username,
                        'last_name': ''
                    }
                )
        return user


class UserUpdateForm(forms.ModelForm):
    """Форма редактирования основных данных пользователя (аватар, email, имя)"""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'avatar']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Имя'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Фамилия'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'name@example.com'}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
        }


class AuthorProfileForm(forms.ModelForm):
    """Форма редактирования биографии и фото автора"""
    class Meta:
        model = Author
        fields = ['bio', 'photo']
        labels = {
            'bio': 'Биография автора',
            'photo': 'Фотография автора',
        }
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Расскажите о своем творческом пути...'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
        }


class CustomPasswordChangeForm(PasswordChangeForm):
    """Стилизованная форма смены пароля"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'