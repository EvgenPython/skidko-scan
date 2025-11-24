from django.db import models
from apps.core.models import Category, Subcategory


class Product(models.Model):
    external_id = models.CharField(
        max_length=255,
        unique=True,
        db_index=True
    )

    # Названия (английское и русское)
    title_en = models.CharField(max_length=500)                      # оригинальный title
    title_ru = models.CharField(max_length=500, blank=True, null=True)  # перевод title

    # SEO-поля (пока не используем)
    seo_title = models.CharField(max_length=255, blank=True, null=True)
    seo_description = models.TextField(blank=True, null=True)
    seo_keywords = models.TextField(blank=True, null=True)

    # Основные данные
    url = models.TextField(null=True, blank=True)
    image_url = models.TextField(null=True, blank=True)

    # Категория (главная)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products"
    )

    # Подкатегория
    subcategory = models.ForeignKey(
        Subcategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products"
    )

    # Цены
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

    # Новое поле — текущая скидка
    discount = models.FloatField(
        default=0.0
    )

    # param – сырые параметры от AliExpress/Admitad
    param = models.TextField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ============================
    #   Разбор параметров param
    # ============================
    def parsed_params(self):
        """
        Возвращает параметры в удобном формате:

        [
            {"icon": "🔥", "label": "Скидка", "value": "69%"},
            {"icon": "💰", "label": "Комиссия", "value": "5.38%"},
            {"icon": "🏪", "label": "ID магазина", "value": "1103726355"},
        ]
        """

        if not self.param:
            return []

        mapping = {
            "discount": {"label": "Скидка", "icon": "🔥"},
            "commissionRate": {"label": "Комиссия", "icon": "💰"},
            "shopId": {"label": "ID магазина", "icon": "🏪"},
        }

        result = []
        rows = self.param.split(";")

        for row in rows:
            if "|" in row:
                parts = row.split("|")
                if len(parts) >= 2:
                    key = parts[0].strip()
                    value = parts[1].strip()

                    if key in mapping:
                        result.append({
                            "icon": mapping[key]["icon"],
                            "label": mapping[key]["label"],
                            "value": value,
                        })

        return result

    def __str__(self):
        return f"{self.title_ru or self.title_en} ({self.external_id})"


class PriceHistory(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="price_history"
    )

    date = models.DateTimeField(auto_now_add=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    discount = models.FloatField(default=0.0)

    def __str__(self):
        return f"{self.product.external_id} — {self.price} ({self.date})"
