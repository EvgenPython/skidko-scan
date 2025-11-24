from django.db import models


class FeedFile(models.Model):

    class Status(models.TextChoices):
        UPLOADED = "uploaded", "Uploaded"
        QUEUED = "queued", "Queued"
        PROCESSING = "processing", "Processing"
        DONE = "done", "Done"
        DUPLICATE = "duplicate", "Duplicate"
        ERROR = "error", "Error"

    file = models.FileField(upload_to="feeds/")
    filename = models.CharField(max_length=255, unique=True)
    feed_date = models.DateField()

    uploaded_at = models.DateTimeField(auto_now_add=True)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.UPLOADED
    )

    progress = models.IntegerField(default=0)
    message = models.TextField(blank=True)

    file_hash = models.CharField(max_length=64, blank=True)

    def __str__(self):
        return f"{self.filename} [{self.status}]"
