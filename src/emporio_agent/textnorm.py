"""Normalização de texto compartilhada (busca / telefone)."""

from __future__ import annotations

import re
import unicodedata


def strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text or "")
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def escape_like(text: str) -> str:
    """Escapa wildcards LIKE e barra invertida para uso com ESCAPE '\\'."""
    return (
        (text or "")
        .replace("\\", "\\\\")
        .replace("%", "\\%")
        .replace("_", "\\_")
    )


def like_pattern(text: str, *, fold_accents: bool = True) -> str:
    value = strip_accents(text) if fold_accents else (text or "")
    return f"%{escape_like(value.strip())}%"


def digits_only(text: str) -> str:
    return "".join(ch for ch in (text or "") if ch.isdigit())


def normalize_phone_digits(phone: str) -> str:
    digits = digits_only(phone)
    if len(digits) >= 12 and digits.startswith("55"):
        digits = digits[2:]
    return digits


_ACCESSORY_HINTS = re.compile(
    r"\b(corda|cordas|palheta|palhetas|cabo|cabos|case|cases|pedal|pedais|"
    r"amplificador|amplificadores|strap|alça|capa)\b",
    re.IGNORECASE,
)


def looks_like_accessory_query(text: str) -> bool:
    return bool(_ACCESSORY_HINTS.search(text or ""))
