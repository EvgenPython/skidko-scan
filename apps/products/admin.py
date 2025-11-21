from django.contrib import admin
from .models import Product, PriceHistory


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'external_id',
        'name',
        'category',
        'price',
        'old_price',
        'currency',
        'created_at',
        'updated_at',
    )

    search_fields = (
        'name',
        'external_id',
        'category__name',
    )

    list_filter = (
        'category',
        'currency',
        'created_at',
    )

    readonly_fields = (
        'id',
        'created_at',
        'updated_at',
    )
