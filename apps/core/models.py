from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models


# --- Категории ---
class Category(models.Model):
    # Английское название — используется для маппинга и логики
    name_en = models.CharField(max_length=255, unique=True)

    # Русское название — отображение на сайте
    name_ru = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ["name_ru", "name_en"]

    def __str__(self):
        return self.name_ru or self.name_en


# --- Подкатегории ---
class Subcategory(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="subcategories"
    )

    # английское имя (как в фидах)
    name_en = models.CharField(max_length=255)

    # русское имя для отображения
    name_ru = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        unique_together = ("category", "name_en")
        ordering = ["name_ru", "name_en"]

    def __str__(self):
        return f"{self.category} → {self.name_ru or self.name_en}"


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
