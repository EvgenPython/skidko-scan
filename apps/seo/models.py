from django.db import models


class SeoTask(models.Model):
    STATUS_CHOICES = [
        ("queued", "Queued"),
        ("processing", "Processing"),
        ("done", "Done"),
        ("error", "Error"),
    ]

    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="queued")

    # Сколько товаров обработать за эту задачу
    limit = models.PositiveIntegerField(default=1000)

    # Сколько уже обработано
    processed = models.PositiveIntegerField(default=0)

    # Текстовое сообщение / ошибки
    message = models.TextField(blank=True)

    def __str__(self):
        return f"SEO Task #{self.id} ({self.status})"

    @property
    def progress(self) -> int:
        if self.limit == 0:
            return 0
        return min(100, int(self.processed * 100 / self.limit))
