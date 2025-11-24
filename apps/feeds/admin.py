from django.contrib import admin
from django.urls import path, reverse
from django.shortcuts import redirect
from django.utils.html import format_html
from django.http import JsonResponse

from .models import FeedFile
from apps.feeds_parser.tasks import process_feed_file_task
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

    class Media:
        js = ('admin/feed_progress.js',)

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

    # ============================
    # КНОПКА "Запустить"
    # ============================
    def process_button(self, obj):
        if not obj.file:
            return format_html('<span style="color:#999;">Файл отсутствует</span>')

        if obj.status == "done":
            return format_html(
                '<span style="color:green;font-weight:bold;">Готово ✔</span>'
            )

        url = reverse('admin:feeds_feedfile_start', args=[obj.pk])
        return format_html(
            '<a class="button" style="padding:4px 10px; background:#28a745; color:white; border-radius:4px;" href="{}">Запустить</a>',
            url,
        )

    process_button.short_description = "Действие"

    # ============================
    # ПРОГРЕСС
    # ============================
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

    # ============================
    # ЗАПУСК ПРОЦЕССА
    # ============================
    def start_processing(self, request, pk):
        feed = FeedFile.objects.get(pk=pk)

        if not feed.file:
            self.message_user(request, "Файл отсутствует.", level="error")
            return redirect('admin:feeds_feedfile_changelist')

        # Ставим status=processing чтобы в UI было видно
        feed.status = "processing"
        feed.progress = 0
        feed.save()

        process_feed_file_task.delay(feed.id)

        self.message_user(request, "Обработка запущена.", level="info")
        return redirect('admin:feeds_feedfile_changelist')

    # ============================
    # ДЛЯ AJAX обновления
    # ============================
    def get_progress_json(self, request, pk):
        feed = FeedFile.objects.get(pk=pk)
        return JsonResponse({
            "status": feed.status,
            "progress": feed.progress,
        })
