from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models


# --- Категории ---
class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class Subcategory(models.Model):
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="subcategories"
    )
    name = models.CharField(max_length=255)

    class Meta:
        unique_together = ("category", "name")

    def __str__(self):
        return f"{self.category.name} → {self.name}"


# --- Магазины ---
class Store(models.Model):
    name = models.CharField(max_length=255)
    logo = models.ImageField(upload_to="store_logos/", null=True, blank=True)
    website = models.URLField(null=True, blank=True)

    def __str__(self):
        return self.name


# --- Пользователи ---
class UserProfile(AbstractUser):
    rating = models.IntegerField(default=0)
    points = models.IntegerField(default=0)

    categories_subscribed = models.ManyToManyField(
        Category, blank=True, related_name='subscribed_users'
    )
    keywords = models.TextField(blank=True, null=True)

    # Исправление конфликтов с AbstractUser
    groups = models.ManyToManyField(
        Group,
        related_name='userprofile_set',
        blank=True,
        verbose_name='groups',
        help_text='The groups this user belongs to.'
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='userprofile_set',
        blank=True,
        verbose_name='user permissions',
        help_text='Specific permissions for this user.'
    )
