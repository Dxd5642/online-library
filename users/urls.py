from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),

    # Редактирование профиля и смена пароля
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
    path('profile/password/', views.change_password_view, name='change_password'),
]