from apps.core.models import Category

def categories_processor(request):
    """
    Глобальный список категорий и подкатегорий.
    """
    categories = (
        Category.objects
        .prefetch_related("subcategories")
        .order_by("name_ru", "name_en")
    )

    # Для каждой категории создаём правильное поле sorted_subcategories
    for cat in categories:
        subcats = list(cat.subcategories.all())
        subcats.sort(key=lambda s: (s.name_ru or "", s.name_en or ""))
        cat.sorted_subcategories = subcats   # <<< ВАЖНО — БЕЗ подчеркивания

    return {
        "categories": categories,
    }
