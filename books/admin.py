from django.contrib import admin
from .models import Genre, Author, Book, FavoriteBook, ReadingProgress, Review


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'user')
    search_fields = ('first_name', 'last_name')


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'file_format', 'uploaded_by', 'created_at')
    list_filter = ('status', 'file_format', 'genres')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}


admin.site.register(FavoriteBook)
admin.site.register(ReadingProgress)
admin.site.register(Review)
