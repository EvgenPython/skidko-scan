from django.shortcuts import render, get_object_or_404
from apps.core.models import Category
from apps.products.models import Product


def category_view(request, slug):
    category = get_object_or_404(Category, slug=slug)

    # Сортировка
    sort = request.GET.get('sort', 'new')

    if sort == 'price_asc':
        products = Product.objects.filter(category=category).order_by('price')
    elif sort == 'price_desc':
        products = Product.objects.filter(category=category).order_by('-price')
    elif sort == 'discount':
        products = (Product.objects
                    .filter(category=category)
                    .extra(select={'discount_value': 'old_price - price'})
                    .order_by('-discount_value'))
    elif sort == 'popular':
        products = Product.objects.filter(category=category).order_by('-id')  # временно
    else:
        products = Product.objects.filter(category=category).order_by('-id')  # новые

    context = {
        "category": category,
        "products": products,
        "sort": sort,
    }

    return render(request, "category.html", context)
