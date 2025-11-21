from django.db import models
from apps.core.models import Category


class Product(models.Model):
    external_id = models.CharField(
        max_length=255,
        unique=True,
        db_index=True
    )

    name = models.CharField(max_length=500)
    url = models.TextField(null=True, blank=True)
    image_url = models.TextField(null=True, blank=True)

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    old_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    currency = models.CharField(
        max_length=20,
        null=True,
        blank=True
    )

    param = models.TextField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.external_id})"


class PriceHistory(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="price_history"
    )

    date = models.DateTimeField(auto_now_add=True)

    price = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    discount = models.FloatField(default=0.0)

    def __str__(self):
        return f"{self.product.external_id} — {self.price} ({self.date})"
