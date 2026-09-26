from django.urls import path
from . import views

app_name = 'books'

urlpatterns = [
    path('', views.book_list_view, name='book_list'),
    path('<int:pk>/', views.book_detail_view, name='book_detail'),
    path('<int:pk>/download/', views.download_book_view, name='book_download'),
    
    # Авторы
    path('create/', views.book_create_view, name='book_create'),
    path('my-books/', views.my_books_view, name='my_books'),
    path('analytics/', views.author_analytics_view, name='author_analytics'), 

    # Избранное / Моя полка
    path('favorites/', views.favorites_list_view, name='favorites_list'),
    path('<int:pk>/favorite/', views.toggle_favorite_view, name='toggle_favorite'),

    # Ридер и прогресс
    path('<int:pk>/read/', views.book_read_view, name='book_read'),
    path('<int:pk>/save-progress/', views.save_reading_progress_view, name='save_progress'),

    # Ридер и сохранение прогресса
    path('<int:pk>/read/', views.book_read_view, name='book_read'),
    path('<int:pk>/save-progress/', views.save_reading_progress_view, name='save_progress'),
    
    # Модерация
    path('moderation/', views.moderator_dashboard_view, name='moderator_dashboard'),
    path('moderation/<int:pk>/', views.moderator_book_detail_view, name='moderator_book_detail'),
    path('moderation/<int:pk>/approve/', views.moderator_approve_book_view, name='moderator_approve'),
    path('moderation/<int:pk>/reject/', views.moderator_reject_book_view, name='moderator_reject'),
    
    # Модерация отзывов
    path('moderation/reviews/<int:pk>/approve/', views.moderator_approve_review_view, name='moderator_approve_review'),
    path('moderation/reviews/<int:pk>/reject/', views.moderator_reject_review_view, name='moderator_reject_review'),]