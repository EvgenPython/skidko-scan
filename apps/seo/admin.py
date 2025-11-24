from django.contrib import admin
from django.db.models import Q
from django.urls import path, reverse
from django.shortcuts import redirect
from django.utils.html import format_html

from apps.products.models import Product
from .models import SeoTask
from .tasks import run_seo_task


@admin.register(SeoTask)
class SeoTaskAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "created_at",
        "status",
        "limit",
        "processed",
        "progress_display",
        "total_products",
        "products_with_seo",
        "products_without_seo",
        "start_button",
    )

    readonly_fields = (
        "created_at",
        "status",
        "processed",
        "progress_readonly",
        "total_products",
        "products_with_seo",
        "products_without_seo",
        "message",
    )

    fields = (
        "created_at",
        "status",
        "limit",
        "processed",
        "progress_readonly",
        "total_products",
        "products_with_seo",
        "products_without_seo",
        "message",
    )

    # --- Кастомные урлы для кнопки "Запустить" ---
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:pk>/start/",
                self.admin_site.admin_view(self.start_task),
                name="seo_seotask_start",
            ),
        ]
        return custom_urls + urls

    # --- Кнопка "Запустить" ---
    def start_button(self, obj):
        url = reverse("admin:seo_seotask_start", args=[obj.pk])
        return format_html(
            '<a class="button" style="padding:4px 10px;" href="{}">Запустить</a>',
            url,
        )

    start_button.short_description = "Действие"

    # --- Прогресс-бар ---
    def progress_display(self, obj):
        color = "#4caf50" if obj.progress >= 100 else "#2196F3"
        return format_html(
            '<div style="width:120px; border:1px solid #ccc; background:#eee">'
            '  <div style="width:{}%; background:{}; color:white; text-align:center;">{}%</div>'
            "</div>",
            obj.progress,
            color,
            obj.progress,
        )

    progress_display.short_description = "Прогресс"

    def progress_readonly(self, obj):
        return self.progress_display(obj)

    progress_readonly.short_description = "Прогресс"

    # --- Статистика по товарам ---
    def total_products(self, obj):
        return Product.objects.count()

    total_products.short_description = "Всего товаров"

    def products_with_seo(self, obj):
        return Product.objects.filter(
            seo_title__isnull=False
        ).exclude(seo_title__exact="").count()

    products_with_seo.short_description = "С SEO"

    def products_without_seo(self, obj):
        return Product.objects.filter(
            Q(seo_title__isnull=True) | Q(seo_title__exact="")
        ).count()

    products_without_seo.short_description = "Без SEO"

    # --- Запуск Celery-задачи ---
    def start_task(self, request, pk):
        task = SeoTask.objects.get(pk=pk)
        task.status = "queued"
        task.processed = 0
        task.message = ""
        task.save()

        run_seo_task.delay(task.id)

        self.message_user(
            request,
            f"SEO-задача #{task.id} отправлена в Celery. "
            f"Будет обработано до {task.limit} товаров без SEO.",
        )
        return redirect("admin:seo_seotask_changelist")
