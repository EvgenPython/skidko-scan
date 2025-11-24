from django.urls import path
from .views import category_view

urlpatterns = [
    path('category/<slug:slug>/', category_view, name='category_page'),
]
