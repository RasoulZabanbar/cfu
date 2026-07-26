# services/phone.py

_PERSIAN_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
_ARABIC_DIGITS = "٠١٢٣٤٥٦٧٨٩"
_ENGLISH_DIGITS = "0123456789"

_DIGIT_TRANSLATION = str.maketrans(
    _PERSIAN_DIGITS + _ARABIC_DIGITS,
    _ENGLISH_DIGITS + _ENGLISH_DIGITS,
)


def to_english_digits(raw: str) -> str:
    """Convert Persian/Arabic-Indic digits to plain ASCII digits."""
    return raw.translate(_DIGIT_TRANSLATION)


def normalize_phone(raw: str) -> str:
    """Normalize to local 0-prefixed format, e.g. 09123456789."""
    p = to_english_digits(raw)
    p = p.strip().replace(" ", "").replace("-", "").replace("‌", "")  # also strip ZWNJ, common in Persian text
    if p.startswith("+98"):
        p = "0" + p[3:]
    elif p.startswith("98") and len(p) > 10:
        p = "0" + p[2:]
    return p