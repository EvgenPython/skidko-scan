# apps/feeds/views.py
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from apps.feeds.models import FeedFile
from apps.feeds_parser.tasks import process_feed_file_task


def feedfile_process(request, pk):
    feedfile = get_object_or_404(FeedFile, pk=pk)

    # Запускаем Celery-задачу
    process_feed_file_task.delay(feedfile.id)

    messages.success(request, f'FeedFile {feedfile.id} отправлен в обработку!')
    # Возврат обратно в список админки
    return redirect('/admin/feeds/feedfile/')
