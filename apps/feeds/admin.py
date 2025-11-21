from django.contrib import admin
from django.urls import path, reverse
from django.shortcuts import redirect
from django.utils.html import format_html
from django.http import JsonResponse

from .models import FeedFile
from apps.feeds_parser.tasks import process_feed_file_task


@admin.register(FeedFile)
class FeedFileAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'file',
        'uploaded_at',
        'status',
        'progress_display',
        'process_button',
    )

    readonly_fields = ('uploaded_at', 'status', 'progress', 'message')

    # ----------------------------------------------------
    # Подключаем JS для автообновления прогресса в админке
    # ----------------------------------------------------
    class Media:
        js = ('admin/feed_progress.js',)

    # ----------------------------------------------------
    # URL маршруты админки
    # ----------------------------------------------------
    def get_urls(self):
        urls = super().get_urls()

        custom_urls = [
            path(
                '<int:pk>/start/',
                self.admin_site.admin_view(self.start_processing),
                name='feeds_feedfile_start'
            ),
            path(
                'progress/<int:pk>/',
                self.admin_site.admin_view(self.get_progress_json),
                name='feeds_feedfile_progress'
            ),
        ]

        return custom_urls + urls

    # ----------------------------------------------------
    # Кнопка "Запустить"
    # ----------------------------------------------------
    def process_button(self, obj):
        url = reverse('admin:feeds_feedfile_start', args=[obj.pk])
        return format_html(
            '<a class="button" style="padding:4px 10px;" href="{}">Запустить</a>',
            url
        )

    process_button.short_description = "Действие"

    # ----------------------------------------------------
    # Прогресс-бар в таблице
    # ----------------------------------------------------
    def progress_display(self, obj):
        color = "#4caf50" if obj.progress == 100 else "#2196F3"

        return format_html(
            '<div style="width:100px; border:1px solid #ccc; background:#eee">'
            '  <div style="width:{}%; background:{}; color:white; text-align:center;">{}%</div>'
            '</div>',
            obj.progress,
            color,
            obj.progress
        )

    progress_display.short_description = "Прогресс"

    # ----------------------------------------------------
    # Запускаем Celery задачу
    # ----------------------------------------------------
    def start_processing(self, request, pk):
        feed = FeedFile.objects.get(pk=pk)

        feed.status = "queued"
        feed.progress = 0
        feed.save()

        # запуск Celery
        process_feed_file_task.delay(feed.id)

        return redirect('admin:feeds_feedfile_changelist')

    # ----------------------------------------------------
    # JSON для AJAX обновления прогресса
    # ----------------------------------------------------
    def get_progress_json(self, request, pk):
        feed = FeedFile.objects.get(pk=pk)

        return JsonResponse({
            "status": feed.status,
            "progress": feed.progress,
        })
