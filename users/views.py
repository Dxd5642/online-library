from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from books.models import Author
from .forms import UserRegisterForm, UserUpdateForm, AuthorProfileForm, CustomPasswordChangeForm



def register_view(request):
    """Представление для регистрации нового пользователя"""
    if request.user.is_authenticated:
        return redirect('users:profile')

    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.username}! Регистрация прошла успешно.')
            return redirect('users:profile')
        else:
            messages.error(request, 'Ошибка при регистрации. Проверьте введенные данные.')
    else:
        form = UserRegisterForm()

    return render(request, 'users/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('users:profile')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'С возвращением, {user.username}!')
            return redirect('users:profile')
        else:
            messages.error(request, 'Неверное имя пользователя или пароль.')
    else:
        form = AuthenticationForm()

    return render(request, 'users/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'Вы успешно вышли из аккаунта.')
    return redirect('users:login')


def profile_view(request):
    if not request.user.is_authenticated:
        return redirect('users:login')
    return render(request, 'users/profile.html')


@login_required
def profile_edit_view(request):
    """Редактирование профиля пользователя и профиля автора"""
    user = request.user
    
    # Получаем или создаем профиль автора для писателей и сотрудников
    author_instance = None
    if getattr(user, 'is_author', False) or getattr(user, 'is_staff', False):
        author_instance, _ = Author.objects.get_or_create(
            user=user,
            defaults={'first_name': user.first_name, 'last_name': user.last_name}
        )

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, request.FILES, instance=user)
        author_form = AuthorProfileForm(request.POST, request.FILES, instance=author_instance) if author_instance else None

        user_valid = user_form.is_valid()
        author_valid = author_form.is_valid() if author_form else True

        if user_valid and author_valid:
            updated_user = user_form.save()
            
            if author_form:
                author_obj = author_form.save(commit=False)
                # Синхронизация имени и фамилии с моделью автора
                author_obj.first_name = updated_user.first_name
                author_obj.last_name = updated_user.last_name
                author_obj.save()

            messages.success(request, 'Профиль успешно обновлен!')
            return redirect('users:profile')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        user_form = UserUpdateForm(instance=user)
        author_form = AuthorProfileForm(instance=author_instance) if author_instance else None

    context = {
        'user_form': user_form,
        'author_form': author_form,
        'is_author': author_instance is not None,
    }
    return render(request, 'users/profile_edit.html', context)


@login_required
def change_password_view(request):
    """Форма смены пароля пользователя"""
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Сохраняем сессию активной
            messages.success(request, 'Пароль успешно изменен!')
            return redirect('users:profile')
    else:
        form = CustomPasswordChangeForm(request.user)

    return render(request, 'users/change_password.html', {'form': form})