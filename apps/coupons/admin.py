from django.contrib import admin
from .models import Coupon


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ("code", "store", "product", "discount_percent", "discount_amount", "active")
    list_filter = ("active", "store")
    search_fields = ("code",)
