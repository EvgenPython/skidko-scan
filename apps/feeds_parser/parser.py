import csv
import io
import logging
import re
from decimal import Decimal

from apps.feeds.models import FeedFile
from apps.core.models import Category
from apps.products.models import Product, PriceHistory

logger = logging.getLogger(__name__)


# -------------------------------------------------------
#  NORMALIZE EXTERNAL ID (SCIENTIFIC NOTATION FIX)
# -------------------------------------------------------
def normalize_external_id(raw_id):
    logger.warning(f"[ID] RAW: {raw_id}")

    if not raw_id:
        logger.warning("[ID] → result: None (empty)")
        return None

    raw_id = raw_id.strip()

    # Excel: "1,00501E+15" → "1.00501E+15"
    cleaned = raw_id.replace(",", ".")
    logger.warning(f"[ID] CLEANED: {cleaned}")

    # Scientific notation
    if re.match(r"^\d+(\.\d+)?[eE][+-]?\d+$", cleaned):
        try:
            num = float(cleaned)
            normalized = str(int(num))
            logger.warning(f"[ID] SCIENTIFIC → {normalized}")
            return normalized
        except Exception as e:
            logger.warning(f"[ID] ERROR scientific convert: {e}")
            return cleaned

    # Just digits
    if cleaned.isdigit():
        logger.warning(f"[ID] DIGITS → {cleaned}")
        return cleaned

    logger.warning(f"[ID] UNKNOWN FORMAT → {cleaned}")
    return cleaned


# -------------------------------------------------------
#  MAIN PARSER FUNCTION
# -------------------------------------------------------
def process_feed_file(feed_id: int):
    print(">>> PROCESS FEED STARTED", flush=True)

    feed = FeedFile.objects.get(id=feed_id)
    errors = []
    processed_count = 0

    logger.warning(f"=== START PROCESS FEED #{feed_id} ===")

    # -------------------------------------------------------
    #  FIX: READ FILE ONCE — AVOID CLOSED FILE ERROR
    # -------------------------------------------------------
    with feed.file.open("rb") as f:
        text_file = io.TextIOWrapper(f, encoding="utf-8", newline="")
        content = text_file.read()

    # Split into lines for DictReader
    lines = content.splitlines()
    total_rows = len(lines) - 1
    if total_rows < 1:
        total_rows = 1

    reader = csv.DictReader(lines, delimiter=';')

    for row in reader:
        try:
            # ---- ID ----
            raw_id = (
                row.get("id")
                or row.get("\ufeffid")
                or row.get("﻿id")
                or None
            )

            external_id = normalize_external_id(raw_id)
            if not external_id:
                raise ValueError("Invalid external ID")

            # ---- FIELDS ----
            name = (row.get("name") or "").strip() or "No name"
            url = row.get("url") or None
            category_name = (row.get("category") or "").strip()

            currency = row.get("currencyId") or None
            param = row.get("param") or None
            image_url = row.get("picture") or None

            price = Decimal(row.get("price") or "0")
            old_price = Decimal(row.get("oldprice") or "0")

            # ---- CATEGORY ----
            category = None
            if category_name:
                category, _ = Category.objects.get_or_create(
                    name=category_name
                )

            # ---- DEBUG ----
            print(
                "=== PRODUCT DEBUG ===",
                external_id,
                name,
                url,
                category_name,
                price,
                old_price,
                flush=True
            )

            # ---- CREATE OR UPDATE PRODUCT ----
            product, created = Product.objects.get_or_create(
                external_id=external_id,
                defaults={
                    "name": name,
                    "url": url,
                    "category": category,
                    "price": price,
                    "old_price": old_price,
                    "currency": currency,
                    "param": param,
                    "image_url": image_url,
                }
            )

            changed = False

            if not created:
                if product.name != name:
                    product.name = name
                    changed = True

                if product.url != url:
                    product.url = url
                    changed = True

                if product.category != category:
                    product.category = category
                    changed = True

                if product.image_url != image_url:
                    product.image_url = image_url
                    changed = True

                if product.currency != currency:
                    product.currency = currency
                    changed = True

                if product.param != param:
                    product.param = param
                    changed = True

                if product.price != price:
                    product.price = price
                    changed = True

                if product.old_price != old_price:
                    product.old_price = old_price
                    changed = True

                if changed:
                    product.save()

            # ---- PRICE HISTORY ----
            last = product.price_history.order_by("-date").first()

            if (not last) or (last.price != price):
                PriceHistory.objects.create(
                    product=product,
                    price=price,
                    discount=0.0,
                )

            processed_count += 1

            # ---- PROGRESS ----
            progress = int(processed_count * 100 / total_rows)
            FeedFile.objects.filter(id=feed.id).update(progress=progress)

        except Exception as e:
            msg = f"{raw_id}: {str(e)}"
            logger.error(msg)
            errors.append(msg)

    # ------------------------------------------------
    #  END
    # ------------------------------------------------
    FeedFile.objects.filter(id=feed.id).update(progress=100)

    feed.refresh_from_db()
    feed.message = f"Processed {processed_count} of {total_rows} items.\n"
    if errors:
        feed.message += "\nErrors:\n" + "\n".join(errors)

    feed.save()
    logger.warning(f"=== END PROCESS FEED #{feed_id} ===")
