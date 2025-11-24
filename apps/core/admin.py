from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Category, Subcategory, Store, UserProfile


# --- Category ---
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name_ru', 'name_en')
    search_fields = ('name_ru', 'name_en')

    ordering = ('name_ru', 'name_en')


# --- Subcategory ---
@admin.register(Subcategory)
class SubcategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name_ru', 'name_en', 'category')
    search_fields = ('name_ru', 'name_en', 'category__name_ru', 'category__name_en')
    list_filter = ('category',)

    ordering = ('category', 'name_ru', 'name_en')


# --- Store ---
@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'website')
    search_fields = ('name',)


# --- UserProfile ---
@admin.register(UserProfile)
class UserProfileAdmin(UserAdmin):
    list_display = (
        'username', 'email', 'first_name', 'last_name',
        'is_staff', 'rating', 'points'
    )
    search_fields = ('username', 'email', 'first_name', 'last_name')

    filter_horizontal = ('categories_subscribed', 'groups', 'user_permissions')
