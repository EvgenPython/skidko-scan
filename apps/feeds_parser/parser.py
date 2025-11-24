import csv
import os
import re
from decimal import Decimal

from django.db import transaction

from apps.feeds.models import FeedFile
from apps.core.models import Category, Subcategory
from apps.products.models import Product, PriceHistory
from apps.products.category_seed_data import CATEGORY_RU
from .translation import translate_batch

# ---------------------------------------------------------
# НАСТРОЙКИ
# ---------------------------------------------------------

# Размер батча товаров (и для перевода, и для bulk-операций)
BATCH_SIZE = 200  # Можно 100 / 200 / 300 – чем больше, тем быстрее

# ---------------------------------------------------------
# КЭШИ В ПАМЯТИ (чтобы не долбить БД)
# ---------------------------------------------------------

CATEGORY_CACHE_BY_EN = {}      # key: name_en.lower() -> Category
SUBCATEGORY_CACHE_BY_EN = {}   # key: subcat_name_en.lower() -> Subcategory

# map подкатегория EN -> основная категория EN
SUBCAT_TO_MAIN = {}            # key: subcat_en.lower() -> main_cat_en
# map category_en -> name_ru
CATEGORY_NAME_RU_MAP = {}      # key: main_cat_en -> name_ru
# map (main_cat_en, subcat_en) -> subcat_ru
SUBCAT_NAME_RU_MAP = {}        # key: (main_cat_en, subcat_en) -> subcat_ru


# ---------------------------------------------------------
# ИНИЦИАЛИЗАЦИЯ МАППИНГА CATEGORY_RU
# ---------------------------------------------------------

def _build_category_mapping_from_seed():
    """
    Готовим вспомогательные словари на основе CATEGORY_RU.
    - SUBCAT_TO_MAIN: "DIY Accessories" -> "Miscellaneous"
    - CATEGORY_NAME_RU_MAP: "Home & Kitchen" -> "Дом и кухня"
    - SUBCAT_NAME_RU_MAP: ("Home & Kitchen","Home Decor") -> "Домашний декор"
    """
    SUBCAT_TO_MAIN.clear()
    CATEGORY_NAME_RU_MAP.clear()
    SUBCAT_NAME_RU_MAP.clear()

    for main_en, meta in CATEGORY_RU.items():
        main_en_clean = main_en.strip()
        main_ru = meta.get("name_ru", main_en_clean)
        CATEGORY_NAME_RU_MAP[main_en_clean] = main_ru

        subcats = meta.get("subcategories", {}) or {}
        for sub_en, sub_ru in subcats.items():
            sub_en_clean = sub_en.strip()
            key_norm = sub_en_clean.lower()
            SUBCAT_TO_MAIN[key_norm] = main_en_clean
            SUBCAT_NAME_RU_MAP[(main_en_clean, sub_en_clean)] = sub_ru


# ---------------------------------------------------------
# КЭШИ CATEGORIES / SUBCATEGORIES
# ---------------------------------------------------------

def _build_initial_caches():
    """
    Один раз за запуск парсера загружаем все категории и подкатегории в память.
    """
    CATEGORY_CACHE_BY_EN.clear()
    SUBCATEGORY_CACHE_BY_EN.clear()

    for c in Category.objects.all():
        key = (c.name_en or "").strip().lower()
        if key:
            CATEGORY_CACHE_BY_EN[key] = c

    for sc in Subcategory.objects.select_related("category"):
        key = (sc.name_en or "").strip().lower()
        if key:
            SUBCATEGORY_CACHE_BY_EN[key] = sc


def _get_or_create_category(main_en: str) -> Category:
    """
    Возвращает Category по английскому имени (с учётом маппинга CATEGORY_RU).
    """
    if not main_en:
        main_en = "Miscellaneous"

    key = main_en.strip().lower()
    cat = CATEGORY_CACHE_BY_EN.get(key)
    if cat:
        return cat

    main_en_clean = main_en.strip()
    main_ru = CATEGORY_NAME_RU_MAP.get(main_en_clean, main_en_clean)

    cat, _ = Category.objects.get_or_create(
        name_en=main_en_clean,
        defaults={"name_ru": main_ru},
    )
    CATEGORY_CACHE_BY_EN[key] = cat
    return cat


def _get_or_create_misc_category() -> Category:
    """
    Специальный helper для 'Miscellaneous'.
    """
    return _get_or_create_category("Miscellaneous")


def resolve_category_and_subcategory(subcat_name_en: str) -> tuple[Category, Subcategory]:
    """
    Главная функция для категорий:

    - На входе только subcategory из фида (например, "DIY Accessories").
    - По маппингу CATEGORY_RU находим основную категорию.
    - Создаём / берём Category и Subcategory из БД.
    """

    if not subcat_name_en:
        # Вообще пусто — кидаем в Miscellaneous / "Без категории"
        cat = _get_or_create_misc_category()
        name_en = "Uncategorized"
        key_norm = name_en.lower()
        sub = SUBCATEGORY_CACHE_BY_EN.get(key_norm)
        if not sub:
            sub, _ = Subcategory.objects.get_or_create(
                category=cat,
                name_en=name_en,
                defaults={"name_ru": "Без категории"},
            )
            SUBCATEGORY_CACHE_BY_EN[key_norm] = sub
        return cat, sub

    clean_sub_en = subcat_name_en.strip()
    key_norm = clean_sub_en.lower()

    # 1. Пытаемся найти подкатегорию в кэше
    sub_cached = SUBCATEGORY_CACHE_BY_EN.get(key_norm)
    if sub_cached:
        return sub_cached.category, sub_cached

    # 2. Пытаемся найти main category через SUBCAT_TO_MAIN
    main_en = SUBCAT_TO_MAIN.get(key_norm)
    if main_en:
        cat = _get_or_create_category(main_en)
        sub_ru = SUBCAT_NAME_RU_MAP.get((main_en, clean_sub_en), clean_sub_en)
    else:
        # Нет в маппинге — кидаем в Miscellaneous
        cat = _get_or_create_misc_category()
        # Попробуем поискать перевод в блоке Miscellaneous, если там есть
        misc_block = CATEGORY_RU.get("Miscellaneous", {})
        misc_subs = misc_block.get("subcategories", {}) or {}
        sub_ru = misc_subs.get(clean_sub_en, clean_sub_en)

    # 3. Создаём / берём Subcategory
    sub, _ = Subcategory.objects.get_or_create(
        category=cat,
        name_en=clean_sub_en,
        defaults={"name_ru": sub_ru},
    )
    SUBCATEGORY_CACHE_BY_EN[key_norm] = sub
    return cat, sub


# ---------------------------------------------------------
# PARSING HELPERS
# ---------------------------------------------------------

def normalize_external_id(val: str | None) -> str | None:
    if not val:
        return None
    val = val.strip().replace(",", ".")
    # На случай научной нотации
    if "e" in val.lower():
        try:
            return str(int(float(val)))
        except Exception:
            return val
    return val


def parse_decimal(v: str | None) -> Decimal | None:
    if not v:
        return None
    v = re.sub(r"[^\d.,-]", "", v)
    v = v.replace(",", ".")
    try:
        return Decimal(v)
    except Exception:
        return None


def parse_discount(param: str | None) -> float:
    """
    param = "discount|61%|;commissionRate|5.38%|;shopId|1104704275|;"
    → 61.0
    """
    if not param:
        return 0.0
    m = re.search(r"discount\|([\d.]+)%", param)
    if m:
        try:
            return float(m.group(1))
        except Exception:
            return 0.0
    return 0.0


def count_total_rows(feed: FeedFile) -> int:
    """
    Лёгкий проход по файлу для подсчёта строк (для прогресса).
    """
    path = feed.file.path
    try:
        with open(path, "r", encoding="utf-8-sig", errors="ignore") as f:
            reader = csv.reader(f, delimiter=";")
            next(reader, None)  # пропускаем заголовок
            return sum(1 for _ in reader)
    except FileNotFoundError:
        return 0


# ---------------------------------------------------------
#  ОБРАБОТКА ОДНОГО БАТЧА
# ---------------------------------------------------------

def _process_batch(rows: list[dict], titles_en: list[str]) -> None:
    """
    Обработка батча:
    - Переводим ТОЛЬКО новые товары (нет Product с таким external_id)
    - Для существующих берём title_ru из БД, не трогаем перевод
    - Новые создаём, существующие обновляем
    - Для всех пишем PriceHistory
    """
    if not rows:
        return

    # 1. Ищем уже существующие продукты по external_id (только среди этого батча)
    ext_ids = [r["external_id"] for r in rows if r.get("external_id")]
    existing_qs = Product.objects.filter(external_id__in=ext_ids)
    existing_by_id = {p.external_id: p for p in existing_qs}

    # 2. Собираем ТОЛЬКО те товары, которых ещё нет в БД → их надо перевести
    titles_to_translate: list[str] = []
    ids_to_translate: list[str] = []

    for row, title_en in zip(rows, titles_en):
        ext_id = row.get("external_id")
        if not ext_id:
            continue
        if ext_id in existing_by_id:
            # Уже есть в БД → НЕ отправляем в translate_batch
            continue
        # Новый товар → нужно перевести
        titles_to_translate.append(title_en)
        ids_to_translate.append(ext_id)

    # 3. Делаем один запрос в OpenAI только для новых товаров
    translation_map: dict[str, str] = {}

    if titles_to_translate:
        titles_ru = translate_batch(titles_to_translate)
        # Защита от рассинхрона длины
        if not titles_ru or len(titles_ru) != len(titles_to_translate):
            titles_ru = titles_to_translate

        for ext_id, title_ru in zip(ids_to_translate, titles_ru):
            translation_map[ext_id] = title_ru

    # 4. Готовим списки для bulk_create / bulk_update / PriceHistory
    new_products: list[Product] = []
    products_to_update: list[Product] = []
    history_items: list[PriceHistory] = []

    # Нам больше не нужен titles_en по индексу — всё берём из rows + translation_map + existing
    for row in rows:
        ext_id = row.get("external_id")
        if not ext_id:
            continue

        existing = existing_by_id.get(ext_id)

        if existing:
            # --- ОБНОВЛЯЕМ СУЩЕСТВУЮЩИЙ ТОВАР ---
            existing.title_en = row["title_en"]
            # ВАЖНО: НЕ ПЕРЕПИСЫВАЕМ title_ru переводом,
            # используем то, что уже было сохранено ранее
            # existing.title_ru остаётся как есть

            existing.url = row["url"]
            existing.image_url = row["image_url"]
            existing.currency = row["currency"]
            existing.price = row["price"]
            existing.old_price = row["old_price"]
            existing.category = row["category"]
            existing.subcategory = row["subcategory"]
            existing.param = row["param"]
            existing.discount = row["discount"]

            products_to_update.append(existing)

            history_items.append(
                PriceHistory(
                    product=existing,
                    price=row["price"],
                    discount=row["discount"],
                )
            )
        else:
            # --- СОЗДАЁМ НОВЫЙ ТОВАР ---
            title_ru = translation_map.get(ext_id, row["title_en"])

            p = Product(
                external_id=ext_id,
                title_en=row["title_en"],
                title_ru=title_ru,
                url=row["url"],
                image_url=row["image_url"],
                currency=row["currency"],
                price=row["price"],
                old_price=row["old_price"],
                category=row["category"],
                subcategory=row["subcategory"],
                param=row["param"],
                discount=row["discount"],
            )
            new_products.append(p)

    # 5. Сохраняем новые продукты
    if new_products:
        Product.objects.bulk_create(new_products, batch_size=2000)
        # После bulk_create надо добавить историю цен и для них
        for p in new_products:
            history_items.append(
                PriceHistory(
                    product=p,
                    price=p.price,
                    discount=p.discount,
                )
            )

    # 6. Обновляем существующие
    if products_to_update:
        Product.objects.bulk_update(
            products_to_update,
            [
                "title_en",
                # "title_ru",  # НЕ трогаем перевод
                "url",
                "image_url",
                "currency",
                "price",
                "old_price",
                "category",
                "subcategory",
                "param",
                "discount",
            ],
            batch_size=2000,
        )

    # 7. bulk_create для истории цен
    if history_items:
        PriceHistory.objects.bulk_create(history_items, batch_size=5000)


# ---------------------------------------------------------
#  ОСНОВНАЯ ФУНКЦИЯ ПАРСЕРА
# ---------------------------------------------------------

def process_feed_file(feed: FeedFile) -> None:
    """
    Главный вход Celery-задачи.

    - Считает строки (для прогресса)
    - Стримит CSV построчно, не загружая всё в память
    - Делит на батчи по BATCH_SIZE
    - По каждому батчу:
        * определяет категорию/подкатегорию
        * переводит названия ТОЛЬКО для новых товаров
        * создаёт / обновляет продукты
        * пишет PriceHistory
    - В конце удаляет файл фида
    """
    file_path = feed.file.path

    # Обновляем статус
    feed.status = FeedFile.Status.PROCESSING
    feed.progress = 0
    feed.message = "Processing..."
    feed.save(update_fields=["status", "progress", "message"])

    # Инициализация маппинга и кэшей категорий
    _build_category_mapping_from_seed()
    _build_initial_caches()

    total_rows = count_total_rows(feed)
    processed = 0

    try:
        with open(file_path, "r", encoding="utf-8-sig", errors="ignore") as f:
            reader = csv.DictReader(f, delimiter=";")

            batch_rows: list[dict] = []
            batch_titles: list[str] = []

            for row in reader:
                processed += 1

                external_id = normalize_external_id(row.get("id"))
                title_en = (row.get("name") or "").strip()
                url = (row.get("url") or "").strip()

                # Это на самом деле ПОДКАТЕГОРИЯ из фида
                subcat_en = (row.get("category") or "").strip()

                currency = (row.get("currencyId") or "").strip()
                param = (row.get("param") or "").strip()
                image_url = (row.get("picture") or "").strip()

                oldprice = parse_decimal(row.get("oldprice"))
                price = parse_decimal(row.get("price"))
                if price and not oldprice:
                    oldprice = price

                discount = parse_discount(param)

                # Категория / подкатегория по маппингу
                category_obj, subcategory_obj = resolve_category_and_subcategory(subcat_en)

                # Кладём в батч
                batch_titles.append(title_en)
                batch_rows.append(
                    {
                        "external_id": external_id,
                        "title_en": title_en,
                        "url": url,
                        "image_url": image_url,
                        "currency": currency,
                        "price": price,
                        "old_price": oldprice,
                        "category": category_obj,
                        "subcategory": subcategory_obj,
                        "param": param,
                        "discount": discount,
                    }
                )

                # Если набрали батч — сохраняем
                if len(batch_rows) >= BATCH_SIZE:
                    _process_batch(batch_rows, batch_titles)
                    batch_rows = []
                    batch_titles = []

                # Обновляем прогресс не по каждой строке, а каждые 500
                if total_rows and processed % 500 == 0:
                    feed.progress = int(processed / total_rows * 100)
                    feed.save(update_fields=["progress"])

            # Хвост батча
            if batch_rows:
                _process_batch(batch_rows, batch_titles)

        # Успешно
        feed.progress = 100
        feed.status = FeedFile.Status.DONE
        feed.message = "Done"
        feed.save(update_fields=["status", "progress", "message"])

    except Exception as e:
        # Если что-то пошло не так — фиксируем в статусе
        feed.status = FeedFile.Status.ERROR
        feed.message = f"Error: {e}"
        feed.save(update_fields=["status", "message"])

    # Удаляем файл после обработки (даже если была ошибка — можно это оставить)
    try:
        os.remove(file_path)
    except Exception:
        pass
