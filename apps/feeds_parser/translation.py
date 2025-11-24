import os
import time
import logging
from typing import List
from openai import OpenAI

logger = logging.getLogger(__name__)

# Кэш: исходное название → перевод
_title_cache: dict[str, str] = {}


def _normalize_title(t: str) -> str:
    return (t or "").strip()


def _get_client() -> OpenAI:
    """
    Создаём клиента OpenAI только при вызове.
    Логируем наличие API-ключа!
    """
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        logger.error("❌ OPENAI_API_KEY is NOT set in Celery environment!")
        raise RuntimeError("OPENAI_API_KEY is not set")

    logger.info(f"🔑 OpenAI API key detected (length={len(api_key)}).")

    return OpenAI(api_key=api_key)


def translate_batch(titles: List[str], batch_size: int = 50) -> List[str]:
    """
    Переводит список title'ов с EN → RU а также печатает подробные логи.
    При ошибках возвращаем оригиналы, но логируем всё.
    """
    clean_titles = [_normalize_title(t) for t in titles]
    logger.warning(f"🟦 [TRANSLATE INPUT] {clean_titles}")

    result: List[str] = []

    for i in range(0, len(clean_titles), batch_size):
        chunk = clean_titles[i: i + batch_size]

        # какие строки ещё не в кэше
        to_translate = [t for t in chunk if t and t not in _title_cache]

        if to_translate:
            logger.info(f"➡️ Переводим {len(to_translate)} товаров...")

            for attempt in range(3):
                try:
                    client = _get_client()

                    user_text_lines = [
                        "Переведи названия товаров с английского на русский.",
                        "Пиши кратко, как для карточки товара в интернет-магазине.",
                        "Каждое название — с новой строки, без номеров, без кавычек.",
                        "",
                        "Вот список товаров:"
                    ] + to_translate

                    user_text = "\n".join(user_text_lines)

                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system",
                             "content": "You are a product title translator for e-commerce (EN→RU)."},
                            {"role": "user", "content": user_text},
                        ],
                        max_tokens=2000,
                    )

                    raw = response.choices[0].message.content or ""
                    lines = [line.strip() for line in raw.split("\n") if line.strip()]

                    if not lines:
                        logger.error("❗ OpenAI вернул ПУСТОЙ ответ!")
                        lines = to_translate[:]   # fallback

                    # Подгоняем длину результата
                    if len(lines) < len(to_translate):
                        logger.warning("⚠️ Количество строк меньше нужного. Дополнил оригиналами.")
                        lines += to_translate[len(lines):]

                    if len(lines) > len(to_translate):
                        lines = lines[:len(to_translate)]

                    # Заполняем кэш
                    for original, translated in zip(to_translate, lines):
                        _title_cache[original] = translated or original

                    logger.info(f"🟩 Успешно переведено: {len(lines)} товаров.")
                    logger.warning(f"🟩 [TRANSLATE OUTPUT] {lines}")

                    break  # успех — выходим из цикла попыток

                except Exception as e:
                    logger.error(f"❌ [OpenAI ERROR] попытка {attempt+1}/3: {e}")
                    time.sleep(2)

                    if attempt == 2:  # 3-я попытка
                        logger.error("❌ Полный провал перевода этого батча! Использую оригиналы.")
                        for original in to_translate:
                            _title_cache[original] = original

        # собираем результат по текущему chunk
        for t in chunk:
            result.append(_title_cache.get(t, t))

    logger.warning(f"🟧 [FINAL TRANSLATE RESULT] {result}")
    return result
