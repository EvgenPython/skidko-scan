from django.contrib import admin
from .models import Product, PriceHistory
from apps.core.models import Category, Subcategory


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):

    # Показываем эти поля в списке
    list_display = (
        'external_id',
        'title_ru',
        'title_en',
        'category',
        'subcategory',
        'price',
        'currency',
        'updated_at',
    )

    # Поиск
    search_fields = (
        'external_id',
        'title_ru',
        'title_en',
        'category__name_ru',
        'category__name_en',
        'subcategory__name_ru',
        'subcategory__name_en',
    )

    # Фильтры
    list_filter = (
        'category',
        'subcategory',
        'currency',
        'updated_at',
    )

    readonly_fields = (
        'id',
        'created_at',
        'updated_at',
    )

    fieldsets = (
        ("Основная информация", {
            "fields": (
                'external_id',
                'title_ru',
                'title_en',
                'url',
                'image_url',
                'category',
                'subcategory',
            )
        }),
        ("Цены", {
            "fields": (
                'price',
                'old_price',
                'currency',
            )
        }),
        ("Дополнительно", {
            "fields": (
                'param',
            )
        }),
        ("Служебные поля", {
            "fields": (
                'created_at',
                'updated_at',
            )
        }),
    )


# --- История цен ---
@admin.register(PriceHistory)
class PriceHistoryAdmin(admin.ModelAdmin):

    list_display = (
        'product',
        'price',
        'discount',
        'date'
    )

    list_filter = (
        'date',
        'discount',
    )

    search_fields = (
        'product__external_id',
        'product__title_ru',
        'product__title_en',
    )

    ordering = ('-date',)
