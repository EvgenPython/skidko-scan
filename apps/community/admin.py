from django.contrib import admin
from .models import Forum, Post, Comment


@admin.register(Forum)
class ForumAdmin(admin.ModelAdmin):
    list_display = ("title", "created_at")
    search_fields = ("title",)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "forum", "user", "created_at")
    list_filter = ("forum", "created_at")
    search_fields = ("title", "content", "user__username")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("post", "user", "created_at")
    list_filter = ("created_at",)
    search_fields = ("content", "user__username")
