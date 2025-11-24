from django.urls import path
from .views import (
    index_view,
    product_detail_view,
    product_search_view,
    category_view,
    subcategory_view,
)

urlpatterns = [
    # Главная
    path("", index_view, name="index"),

    # Товар
    path("product/<int:pk>/", product_detail_view, name="product_detail"),

    # Поиск
    path("search/", product_search_view, name="product_search"),

    # Категории
    path("category/<int:pk>/", category_view, name="category_view"),

    # Подкатегории
    path("subcategory/<int:pk>/", subcategory_view, name="subcategory_view"),
]
