from django.shortcuts import get_object_or_404, redirect
from django.contrib import admin
from .models import FeedFile

def process_feed_file(request, pk):
    feed_file = get_object_or_404(FeedFile, pk=pk)
    # Здесь твоя логика обработки файла
    # Например: process_feed(feed_file)

    # После обработки перенаправляем обратно в список
    return redirect('/admin/feeds_parser/feedfile/')
