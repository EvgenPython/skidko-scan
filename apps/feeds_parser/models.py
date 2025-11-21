# apps/feeds_parser/models.py
from django.db import models

class FeedFile(models.Model):
    title = models.CharField(max_length=255)  # для отображения в админке
    file = models.FileField(upload_to='feeds/')  # сам фид
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
