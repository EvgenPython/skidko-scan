from django.db import models
from ..core.models import UserProfile
from ..products.models import Product


class UserProduct(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name="user_products")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="user_products")
    added_at = models.DateTimeField(auto_now_add=True)
    favorite = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.product.name_en}"
