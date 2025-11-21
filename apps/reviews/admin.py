from django.contrib import admin
from .models import ProductReview, DiscountConfirmation


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ("product", "user", "rating", "created_at")
    list_filter = ("rating", "created_at")
    search_fields = ("product__name_en", "user__username")


@admin.register(DiscountConfirmation)
class DiscountConfirmationAdmin(admin.ModelAdmin):
    list_display = ("product", "user", "confirmed")
    list_filter = ("confirmed",)
