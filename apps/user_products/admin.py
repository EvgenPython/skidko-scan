from django.contrib import admin
from .models import UserProduct

@admin.register(UserProduct)
class UserProductAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "favorite", "added_at")
    list_filter = ("favorite", "added_at")
    search_fields = ("user__username", "product__name_en")
