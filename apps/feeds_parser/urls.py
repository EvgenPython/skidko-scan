from django.urls import path
from . import admin_views  # отдельный файл для админских вьюшек

app_name = 'feeds_parser'

urlpatterns = [
    path('feedfile/<int:pk>/process/', admin_views.process_feedfile, name='feeds_feedfile_process'),
]