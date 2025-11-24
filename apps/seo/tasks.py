from celery import shared_task
from django.db.models import Q

from apps.products.models import Product
from .models import SeoTask
from .services import generate_seo_batch


@shared_task
def run_seo_task(seo_task_id: int):
    """
    Celery-задача:
    - Берёт SeoTask по id
    - Находит товары БЕЗ seo_title
    - Обрабатывает не больше task.limit штук
    - Записывает SEO-поля в Product
    """
    task = SeoTask.objects.get(id=seo_task_id)

    task.status = "processing"
    task.processed = 0
    task.message = ""
    task.save()

    # Товары без SEO
    qs = Product.objects.filter(
        Q(seo_title__isnull=True) | Q(seo_title__exact="")
    ).order_by("id")

    total_to_process = min(task.limit, qs.count())

    if total_to_process == 0:
        task.status = "done"
        task.message = "Нет товаров без SEO."
        task.save()
        return

    processed = 0

    batch_size = 20

    while processed < total_to_process:
        # от processed до processed + batch_size
        batch_qs = qs[processed: processed + batch_size]
        products = list(batch_qs)
        if not products:
            break

        # для SEO используем translated_name если есть, иначе name
        titles = [p.translated_name or p.name for p in products]

        seo_list = generate_seo_batch(titles)

        for product, seo_data in zip(products, seo_list):
            product.seo_title = seo_data.get("seo_title") or product.seo_title
            product.seo_description = seo_data.get("seo_description") or product.seo_description
            product.seo_keywords = seo_data.get("seo_keywords") or product.seo_keywords
            product.save(update_fields=["seo_title", "seo_description", "seo_keywords"])

        processed += len(products)
        task.processed = processed
        task.save(update_fields=["processed"])

    task.status = "done"
    task.save(update_fields=["status"])
