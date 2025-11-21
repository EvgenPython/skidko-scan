# apps/feeds/urls.py
from django.urls import path
from . import views

app_name = 'feeds'  # namespace для reverse

urlpatterns = [
    path('feedfile/<int:pk>/process/', views.feedfile_process, name='feedfile_process'),
]
