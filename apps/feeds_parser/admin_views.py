from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import FeedFile

def process_feedfile(request, pk):
    feed_file = get_object_or_404(FeedFile, pk=pk)

    # Тут твоя логика обработки
    # Например, можно вызвать Celery задачу:
    # from .tasks import process_feed_file_task
    # process_feed_file_task.delay(feed_file.id)

    messages.success(request, f'FeedFile {feed_file.id} обработан.')
    return redirect('admin:feeds_parser_feedfile_changelist')
