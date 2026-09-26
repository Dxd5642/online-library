from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ['username', 'email', 'role', 'is_staff', 'is_active']
    
    # Добавляем наше поле role и avatar в форму редактирования пользователя в админке
    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительные поля', {'fields': ('role', 'avatar')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Дополнительные поля', {'fields': ('role', 'avatar')}),
    )