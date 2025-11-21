from django.db import models


class FeedFile(models.Model):
    file = models.FileField(upload_to="feeds/")
    filename = models.CharField(max_length=255, unique=True)
    feed_date = models.DateField()

    uploaded_at = models.DateTimeField(auto_now_add=True)

    status = models.CharField(
        max_length=20,
        choices=[
            ("uploaded", "Uploaded"),      # файл загружен
            ("queued", "Queued"),          # задача отправлена в Celery
            ("processing", "Processing"),  # Celery обрабатывает
            ("done", "Done"),              # завершено
            ("duplicate", "Duplicate"),    # дубль файла
            ("error", "Error")             # ошибка
        ],
        default="uploaded"
    )

    # 🔥 ПРОГРЕСС: от 0 до 100 (обязательно!)
    progress = models.IntegerField(default=0)

    # текстовое сообщение, ошибки и т.п.
    message = models.TextField(blank=True)

    # хеш файла (твой функционал)
    file_hash = models.CharField(max_length=64, blank=True)

    def __str__(self):
        return f"{self.filename} [{self.status}]"
