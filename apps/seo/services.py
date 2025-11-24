import os
import time
from typing import List, Dict

from openai import OpenAI

# Кэш: исходный заголовок → SEO-данные
_seo_cache: dict[str, Dict[str, str]] = {}


def _normalize_title(t: str) -> str:
    return (t or "").strip()


def _get_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    return OpenAI(api_key=api_key)


def generate_seo_batch(titles: List[str], batch_size: int = 20) -> List[Dict[str, str]]:
    """
    На будущее: генерирует SEO для списка заголовков (EN/RU).
    Сейчас это можно не запускать, пока не будешь готов тратить деньги.
    Возвращает список словарей:
    {
        "seo_title": "...",
        "seo_description": "...",
        "seo_keywords": "..."
    }
    """
    clean_titles = [_normalize_title(t) for t in titles]
    result: List[Dict[str, str]] = []

    for i in range(0, len(clean_titles), batch_size):
        chunk = clean_titles[i: i + batch_size]

        to_process = [t for t in chunk if t and t not in _seo_cache]

        if to_process:
            for attempt in range(3):
                try:
                    client = _get_client()

                    lines = [
                        "У тебя список названий товаров.",
                        "Для КАЖДОГО товара на русском сделай:",
                        "1) SEO title (до 100 символов).",
                        "2) SEO description (до 200 символов).",
                        "3) SEO keywords (5–10 ключевых слов через запятую).",
                        "",
                        "Формат ответа СТРОГО такой, одна строка на товар:",
                        "<seo_title>|||<seo_description>|||<seo_keywords>",
                        "",
                        "Никакого лишнего текста до или после списка.",
                        "Вот список товаров:",
                    ]
                    lines.extend(to_process)
                    user_text = "\n".join(lines)

                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {
                                "role": "system",
                                "content": (
                                    "You are a professional Russian-speaking SEO copywriter for an e-commerce site."
                                ),
                            },
                            {"role": "user", "content": user_text},
                        ],
                        max_tokens=3000,
                    )

                    raw = response.choices[0].message.content or ""
                    resp_lines = [line.strip() for line in raw.split("\n") if line.strip()]

                    if len(resp_lines) < len(to_process):
                        resp_lines += [""] * (len(to_process) - len(resp_lines))
                    elif len(resp_lines) > len(to_process):
                        resp_lines = resp_lines[:len(to_process)]

                    for original, line in zip(to_process, resp_lines):
                        parts = [p.strip() for p in line.split("|||")]
                        while len(parts) < 3:
                            parts.append("")

                        seo_title, seo_description, seo_keywords = parts

                        if not seo_title:
                            seo_title = original

                        data = {
                            "seo_title": seo_title,
                            "seo_description": seo_description,
                            "seo_keywords": seo_keywords,
                        }
                        _seo_cache[original] = data

                    break

                except Exception as e:
                    print(f"[OpenAI][SEO] Ошибка батча (попытка {attempt + 1}/3): {e}", flush=True)
                    time.sleep(2)

                    if attempt == 2:
                        for original in to_process:
                            if original not in _seo_cache:
                                _seo_cache[original] = {
                                    "seo_title": original,
                                    "seo_description": "",
                                    "seo_keywords": "",
                                }

        # собираем результат для chunk
        for t in chunk:
            if not t:
                result.append(
                    {
                        "seo_title": "",
                        "seo_description": "",
                        "seo_keywords": "",
                    }
                )
            else:
                data = _seo_cache.get(
                    t,
                    {
                        "seo_title": t,
                        "seo_description": "",
                        "seo_keywords": "",
                    },
                )
                result.append(data)

    return result
