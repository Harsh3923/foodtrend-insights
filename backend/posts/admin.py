from django.contrib import admin
from .models import Post, Term, PostTerm

# Register your models here.
@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("reddit_id", "subreddit", "created_utc", "score", "num_comments")
    list_filter = ("subreddit",)
    search_fields = ("reddit_id", "title")

@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    list_display = ("text", "is_active")
    list_filter = ("is_active",)
    search_fields = ("text",)

@admin.register(PostTerm)
class PostTermAdmin(admin.ModelAdmin):
    list_display = ("term", "post", "created_at")
    search_fields = ("term__text", "post__reddit_id", "post__title")