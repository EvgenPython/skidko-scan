from django.db import models
from ..core.models import UserProfile
from ..products.models import Product


class ProductReview(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    rating = models.IntegerField(default=5)
    text = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(UserProfile, blank=True, related_name="liked_reviews")
    image = models.ImageField(upload_to="review_images/", null=True, blank=True)

    def __str__(self):
        return f"Review by {self.user.username} for {self.product.name_en}"


class DiscountConfirmation(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="discount_confirmations")
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    confirmed = models.BooleanField()

    def __str__(self):
        return f"{self.user.username} {'confirmed' if self.confirmed else 'rejected'} {self.product.name_en}"
