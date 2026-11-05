# -*- coding: utf-8 -*-
"""Генерация / выбор капчи."""
from __future__ import annotations

import os
import random
import string
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter

import config

_ALPHABET = string.ascii_uppercase + string.digits
# убираем похожие символы
_ALPHABET = "".join(c for c in _ALPHABET if c not in "O0IL1")


def _random_code(length: int = None) -> str:
    length = length or config.CAPTCHA_LENGTH
    return "".join(random.choices(_ALPHABET, k=length))


def _generate_image(code: str) -> bytes:
    w, h = 240, 90
    img = Image.new("RGB", (w, h), (20, 22, 30))
    draw = ImageDraw.Draw(img)

    # шум
    for _ in range(400):
        x, y = random.randint(0, w - 1), random.randint(0, h - 1)
        draw.point((x, y), fill=(random.randint(40, 90),) * 3)

    # линии
    for _ in range(5):
        draw.line(
            [
                (random.randint(0, w), random.randint(0, h)),
                (random.randint(0, w), random.randint(0, h)),
            ],
            fill=(random.randint(60, 120),) * 3,
            width=2,
        )

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 42)
    except Exception:
        font = ImageFont.load_default()

    # буквы с лёгким смещением
    x = 20
    for ch in code:
        y = random.randint(15, 30)
        color = (random.randint(180, 255), random.randint(180, 255), random.randint(100, 200))
        draw.text((x, y), ch, font=font, fill=color)
        x += 50

    img = img.filter(ImageFilter.SMOOTH)
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def get_captcha() -> tuple[str, bytes]:
    """
    Возвращает (answer, png_bytes).
    Если в CAPTCHA_DIR есть файлы — берёт случайный (имя файла = ответ).
    Иначе генерирует на лету.
    """
    captcha_dir = Path(config.CAPTCHA_DIR)
    if captcha_dir.is_dir():
        files = [f for f in captcha_dir.iterdir() if f.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}]
        if files:
            f = random.choice(files)
            answer = f.stem.upper()
            return answer, f.read_bytes()

    code = _random_code()
    return code, _generate_image(code)
