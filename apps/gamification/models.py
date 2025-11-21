from django.db import models
from ..core.models import UserProfile


class Achievement(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    points = models.IntegerField(default=0)

    def __str__(self):
        return self.name


class UserAchievement(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name="achievements")
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    unlocked_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.achievement.name}"
