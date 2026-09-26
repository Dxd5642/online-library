from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Avg, Sum, Count, F
from django.contrib import messages
from .forms import BookForm, ReviewForm
from .models import Book, Author, Genre, Review
import json
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from .models import Book, Genre, Review, ReadingProgress, FavoriteBook


def download_book_view(request, pk):
    """Инкремент счетчика скачиваний и перенаправление на файл книги"""
    book = get_object_or_404(Book, pk=pk, status=Book.Status.PUBLISHED)
    Book.objects.filter(pk=pk).update(downloads_count=book.downloads_count + 1)
    return redirect(book.file.url)


@login_required
def book_read_view(request, pk: int):
    """Страница онлайн-ридера книги"""
    book = get_object_or_404(Book, pk=pk, status=Book.Status.PUBLISHED)

    # Проверяем, прикреплен ли файл к модели
    if not book.file:
        raise Http404("Файл книги отсутствует.")

    # Получаем или создаем запись прогресса чтения для текущего пользователя
    progress, _ = ReadingProgress.objects.get_or_create(
        user=request.user,
        book=book,
        defaults={'last_page': 1}
    )

    context = {
        'book': book,
        'start_page': progress.last_page,
    }
    return render(request, 'books/book_reader.html', context)

@login_required
def my_books_view(request):
    """Список всех загруженных пользователем книг"""
    books = Book.objects.filter(
        Q(uploaded_by=request.user) | Q(authors__user=request.user)
    ).distinct().order_by('-created_at')
    
    return render(request, 'books/my_books.html', {'books': books})

@login_required
@require_POST
def save_reading_progress_view(request, pk):
    """AJAX-эндпоинт для сохранения текущей страницы"""
    book = get_object_or_404(Book, pk=pk)
    
    try:
        data = json.loads(request.body)
        page_number = int(data.get('page', 1))

        if page_number < 1:
            return JsonResponse({'status': 'error', 'message': 'Некорректный номер страницы'}, status=400)

        progress, _ = ReadingProgress.objects.get_or_create(user=request.user, book=book)
        progress.last_page = page_number
        progress.save()

        return JsonResponse({'status': 'success', 'page': page_number})
    except (ValueError, TypeError, json.JSONDecodeError):
        return JsonResponse({'status': 'error', 'message': 'Неверный формат данных'}, status=400)


def book_list_view(request):
    """Каталог с поиском, фильтрацией по жанрам/форматам и сортировкой"""
    # Аннотируем книги средним рейтингом только одобренных отзывов
    books = Book.objects.filter(status=Book.Status.PUBLISHED).annotate(
        avg_rating=Avg('reviews__rating', filter=Q(reviews__is_approved=True))
    ).prefetch_related('authors', 'genres')

    # 1. Поиск по названию или автору
    query = request.GET.get('q', '').strip()
    if query:
        books = books.filter(
            Q(title__icontains=query) |
            Q(authors__first_name__icontains=query) |
            Q(authors__last_name__icontains=query)
        ).distinct()

    # 2. Фильтрация по жанру
    selected_genre = None
    selected_genre_slug = request.GET.get('genre')
    if selected_genre_slug:
        books = books.filter(genres__slug=selected_genre_slug)
        selected_genre = Genre.objects.filter(slug=selected_genre_slug).first()

    # 3. Фильтрация по формату
    selected_format = request.GET.get('format', '')
    if selected_format in [Book.Format.PDF, Book.Format.EPUB, Book.Format.FB2]:
        books = books.filter(file_format=selected_format)

    # 4. Сортировка
    sort_by = request.GET.get('sort', 'newest')
    if sort_by == 'views':
        books = books.order_by('-views_count', '-created_at')
    elif sort_by == 'downloads':
        books = books.order_by('-downloads_count', '-created_at')
    elif sort_by == 'rating':
        books = books.order_by('-avg_rating', '-created_at')
    else:
        sort_by = 'newest'
        books = books.order_by('-created_at')

    genres = Genre.objects.all()

    # Список ID избранных книг текущего пользователя
    user_favorite_ids = []
    if request.user.is_authenticated:
        user_favorite_ids = list(
            FavoriteBook.objects.filter(user=request.user).values_list('book_id', flat=True)
        )

    context = {
        'books': books,
        'genres': genres,
        'selected_genre': selected_genre,
        'selected_format': selected_format,
        'sort_by': sort_by,
        'query': query,
        'user_favorite_ids': user_favorite_ids,
        'formats': Book.Format.choices,
    }
    return render(request, 'books/book_list.html', context)


def book_detail_view(request, pk):
    """Детальная страница книги со статусом избранного, отзывами и формой добавления"""
    book = get_object_or_404(
        Book.objects.prefetch_related('authors', 'genres'),
        pk=pk,
        status=Book.Status.PUBLISHED
    )

    # Обработка отправки отзыва
    review_form = None
    if request.user.is_authenticated:
        if request.method == 'POST':
            review_form = ReviewForm(request.POST)
            if review_form.is_valid():
                review = review_form.save(commit=False)
                review.book = book
                review.user = request.user

                # Проверка прав модератора/персонала
                is_moderator = getattr(request.user, 'is_moderator', False) or request.user.is_staff
                if is_moderator:
                    review.is_approved = True
                    messages.success(request, 'Ваш отзыв успешно опубликован!')
                else:
                    review.is_approved = False
                    messages.success(request, 'Ваш отзыв отправлен и появится после проверки модератором.')

                review.save()
                return redirect('books:book_detail', pk=book.pk)
        else:
            review_form = ReviewForm()

    # Атомарный инкремент счетчика просмотров
    Book.objects.filter(pk=pk).update(views_count=F('views_count') + 1)

    # Список одобренных отзывов
    reviews = book.reviews.filter(is_approved=True).select_related('user')

    # Статус избранного и личный отзыв текущего пользователя
    user_review = None
    is_favorite = False
    if request.user.is_authenticated:
        user_review = book.reviews.filter(user=request.user).first()
        is_favorite = FavoriteBook.objects.filter(user=request.user, book=book).exists()

    # Расчет среднего рейтинга
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']
    avg_rating = round(avg_rating, 1) if avg_rating else None

    context = {
        'book': book,
        'reviews': reviews,
        'user_review': user_review,
        'review_form': review_form,
        'avg_rating': avg_rating,
        'is_favorite': is_favorite,
    }
    return render(request, 'books/book_detail.html', context)




# ======= Moderator panel =========


@login_required
def moderator_dashboard_view(request):
    """Панель модерации с вкладками для книг и отзывов"""
    # Проверка прав доступа модератора или администратора
    is_moderator = getattr(request.user, 'is_moderator', False) or request.user.is_staff
    if not is_moderator:
        messages.error(request, 'У вас нет прав для доступа к панели модерации.')
        return redirect('users:profile')

    active_tab = request.GET.get('tab', 'books')

    # Оптимизация запросов: select_related предотвращает N+1 проблемы при рендере авторов/пользователей
    pending_books = (
        Book.objects.filter(status=Book.Status.PENDING)
        .select_related('uploaded_by')
        .order_by('-created_at')
    )
    
    pending_reviews = (
        Review.objects.filter(is_approved=False)
        .select_related('user', 'book')
        .order_by('-created_at')
    )

    context = {
        'active_tab': active_tab,
        'books': pending_books,
        'reviews': pending_reviews,
        'pending_books_count': pending_books.count(),
        'pending_reviews_count': pending_reviews.count(),
    }
    return render(request, 'books/moderator_dashboard.html', context)


@login_required
def moderator_book_detail_view(request, pk):
    """Детальная страница проверки книги модератором"""
    # Проверка прав доступа модератора или администратора
    is_moderator = getattr(request.user, 'is_moderator', False) or request.user.is_staff
    if not is_moderator:
        messages.error(request, 'У вас нет прав для доступа к панели модерации.')
        return redirect('users:profile')

    # Оптимизация: предварительная загрузка автора загрузки (select_related)
    # и M2M связей авторов/жанров (prefetch_related) для исключения N+1 запросов
    book = get_object_or_404(
        Book.objects.select_related('uploaded_by').prefetch_related('authors', 'genres'),
        pk=pk
    )

    return render(request, 'books/moderator_book_detail.html', {'book': book})


@login_required
def moderator_approve_book_view(request, pk):
    """Одобрение книги"""
    if not request.user.is_moderator:
        return redirect('users:profile')

    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        book.status = Book.Status.PUBLISHED
        book.save()
        messages.success(request, f'Книга "{book.title}" успешно опубликована!')
    return redirect('books:moderator_dashboard')


@login_required
def moderator_reject_book_view(request, pk):
    """Отклонение книги"""
    if not request.user.is_moderator:
        return redirect('users:profile')

    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        book.status = Book.Status.REJECTED
        book.save()
        messages.warning(request, f'Книга "{book.title}" отклонена.')
    return redirect('books:moderator_dashboard')


@login_required
def moderator_approve_review_view(request, pk):
    """Одобрение отзыва"""
    if not request.user.is_moderator:
        return redirect('users:profile')

    review = get_object_or_404(Review, pk=pk)
    if request.method == 'POST':
        review.is_approved = True
        review.save()
        messages.success(request, f'Отзыв от {review.user.username} успешно опубликован!')
    return redirect('/books/moderation/?tab=reviews')


@login_required
def moderator_reject_review_view(request, pk):
    """Отклонение (удаление) отзыва"""
    if not request.user.is_moderator:
        return redirect('users:profile')

    review = get_object_or_404(Review, pk=pk)
    if request.method == 'POST':
        review.delete()
        messages.warning(request, f'Отзыв от {review.user.username} отклонен и удален.')
    return redirect('/books/moderation/?tab=reviews')



# ========= Author ==========
@login_required
def book_create_view(request):
    # Проверка прав доступа
    if not (
        request.user.is_author
        or request.user.is_moderator
        or request.user.is_staff
    ):
        messages.error(
            request,
            'У вас нет прав для добавления книг. Зарегистрируйтесь как автор.',
        )
        return redirect('users:profile')

    if request.method == 'POST':
        form = BookForm(
            request.POST,
            request.FILES,
            user=request.user
        )

        if form.is_valid():
            book = form.save(commit=False, user=request.user)
            book.save()
            form.save_m2m()

            if hasattr(request.user, 'author_profile'):
                book.authors.add(request.user.author_profile)

            messages.success(
                request,
                f'Книга «{book.title}» успешно отправлена на модерацию!'
            )

            return redirect('users:profile')

    else:
        form = BookForm(user=request.user)

    return render(request, 'books/book_form.html', {'form': form})

@login_required
def author_analytics_view(request):
    """Панель аналитики и статистики автора"""
    if not (request.user.is_author or request.user.is_moderator or request.user.is_staff):
        messages.error(request, 'Аналитика доступна только для авторов.')
        return redirect('users:profile')

    user_books = Book.objects.filter(
        Q(uploaded_by=request.user) | Q(authors__user=request.user)
    ).distinct().annotate(
        book_avg_rating=Avg('reviews__rating', filter=Q(reviews__is_approved=True)),
        reviews_count=Count('reviews', filter=Q(reviews__is_approved=True))
    ).order_by('-created_at')

    total_views = user_books.aggregate(Sum('views_count'))['views_count__sum'] or 0
    total_downloads = user_books.aggregate(Sum('downloads_count'))['downloads_count__sum'] or 0
    total_books = user_books.count()

    author_avg_rating = Review.objects.filter(
        book__in=user_books, 
        is_approved=True
    ).aggregate(Avg('rating'))['rating__avg']
    author_avg_rating = round(author_avg_rating, 1) if author_avg_rating else 0.0

    chart_labels = [book.title[:20] + ('...' if len(book.title) > 20 else '') for book in user_books]
    chart_views = [book.views_count for book in user_books]
    chart_downloads = [book.downloads_count for book in user_books]

    context = {
        'user_books': user_books,
        'total_views': total_views,
        'total_downloads': total_downloads,
        'total_books': total_books,
        'author_avg_rating': author_avg_rating,
        'chart_labels': json.dumps(chart_labels, ensure_ascii=False),
        'chart_views': json.dumps(chart_views),
        'chart_downloads': json.dumps(chart_downloads),
    }
    return render(request, 'books/author_analytics.html', context)

# ==================== ИЗБРАННОЕ / МОЯ ПОЛКА ====================

@login_required
@require_POST
def toggle_favorite_view(request, pk):
    """AJAX-переключатель добавления/удаления из избранного"""
    book = get_object_or_404(Book, pk=pk)
    favorite, created = FavoriteBook.objects.get_or_create(user=request.user, book=book)

    if not created:
        favorite.delete()
        is_favorite = False
        message = 'Книга удалена из избранного'
    else:
        is_favorite = True
        message = 'Книга добавлена в избранное'

    return JsonResponse({'status': 'success', 'is_favorite': is_favorite, 'message': message})


@login_required
def favorites_list_view(request):
    """Страница «Моя полка / Избранное»"""
    favorites = FavoriteBook.objects.filter(user=request.user).select_related('book').order_by('-added_at')
    return render(request, 'books/favorites.html', {'favorites': favorites})