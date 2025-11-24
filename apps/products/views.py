from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils.dateformat import DateFormat

from apps.products.models import Product
from apps.core.models import Category, Subcategory


# ============================
#       ГЛАВНАЯ СТРАНИЦА
# ============================
def index_view(request):
    """
    Главная страница.
    Показываем только товары, у которых есть title_ru.
    """
    products = Product.objects.filter(
        title_ru__isnull=False
    ).exclude(
        title_ru=""
    ).order_by("-id")

    paginator = Paginator(products, 50)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "index.html", {
        "page_obj": page_obj,
        "products": page_obj.object_list,
    })


# ============================
#       ПРОДУКТ
# ============================
def product_detail_view(request, pk):
    product = get_object_or_404(Product, pk=pk)

    history = product.price_history.order_by("date")
    labels = [DateFormat(h.date).format("d.m.Y") for h in history]
    values = [float(h.price) for h in history]

    # 🔥 Расчёт скидки (если есть old_price)
    discount = None
    if product.old_price and product.old_price > product.price:
        discount = round(((product.old_price - product.price) / product.old_price) * 100)

    return render(request, "product.html", {
        "product": product,
        "price_history": history,
        "labels": labels,
        "values": values,
        "discount": discount,   # << добавили
    })



# ============================
#          ПОИСК
# ============================
def product_search_view(request):
    q = request.GET.get("q", "").strip()

    products = Product.objects.filter(
        title_ru__isnull=False
    ).exclude(
        title_ru=""
    ).filter(
        Q(title_ru__icontains=q) | Q(title_en__icontains=q)
    ).order_by("-id")

    return render(request, "search.html", {
        "products": products,
        "search_query": q,
    })


# ============================
#     СТРАНИЦА КАТЕГОРИИ
# ============================
def category_view(request, pk):
    """
    Страница категории.
    Фильтр по категориям, сортировка, пагинация.
    """
    category = get_object_or_404(Category, pk=pk)

    products = Product.objects.filter(category=category)

    # сортировка
    sort = request.GET.get("sort")

    if sort == "price_asc":
        products = products.order_by("price")
    elif sort == "price_desc":
        products = products.order_by("-price")
    elif sort == "discount":
        products = products.order_by("-old_price")
    elif sort == "popular":
        products = products.annotate(ph_count=Count("price_history")).order_by("-ph_count")
    elif sort == "new":
        products = products.order_by("-id")
    else:
        products = products.order_by("-id")

    # пагинация
    paginator = Paginator(products, 50)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "category.html", {
        "category": category,
        "products": page_obj.object_list,
        "page_obj": page_obj,
        "sort": sort,
    })


# ============================
#    СТРАНИЦА ПОДКАТЕГОРИИ
# ============================
def subcategory_view(request, pk):
    """
    Страница подкатегории.
    """
    subcategory = get_object_or_404(Subcategory, pk=pk)

    products = Product.objects.filter(subcategory=subcategory).order_by("-id")

    # сортировка
    sort = request.GET.get("sort")
    if sort == "price_asc":
        products = products.order_by("price")
    elif sort == "price_desc":
        products = products.order_by("-price")
    elif sort == "discount":
        products = products.order_by("-old_price")
    elif sort == "popular":
        products = products.annotate(ph_count=Count("price_history")).order_by("-ph_count")
    elif sort == "new":
        products = products.order_by("-id")

    paginator = Paginator(products, 50)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "subcategory.html", {
        "subcategory": subcategory,
        "category": subcategory.category,
        "products": page_obj.object_list,
        "page_obj": page_obj,
        "sort": sort,
    })
