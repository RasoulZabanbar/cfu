import re

_PERSIAN_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
_ARABIC_DIGITS = "٠١٢٣٤٥٦٧٨٩"
_ENGLISH_DIGITS = "0123456789"
_DIGIT_TRANSLATION = str.maketrans(
    _PERSIAN_DIGITS + _ARABIC_DIGITS,
    _ENGLISH_DIGITS + _ENGLISH_DIGITS,
)


def normalize_phone(raw) -> str:
    """
    Normalize any Iranian mobile number representation to the canonical
    local form: '0' + 10 digits, e.g. '09012844143'.

    Handles, all producing the SAME output '09012844143':
      +989012844143
      00989012844143
      989012844143
      9012844143       <- bare 10 digits, no leading 0 (the bug case)
      09012844143
      with spaces/dashes/zero-width-non-joiner
      with Persian/Arabic-Indic digits
    """
    if raw is None:
        return ""

    p = str(raw).translate(_DIGIT_TRANSLATION)
    p = p.strip().replace(" ", "").replace("-", "").replace("\u200c", "")
    p = re.sub(r"[^\d+]", "", p)  # strip anything that isn't a digit or +

    if not p:
        return ""

    # Strip country code in any of its forms down to the bare national number
    if p.startswith("+98"):
        p = p[3:]
    elif p.startswith("0098"):
        p = p[4:]
    elif p.startswith("98") and len(p) == 12:
        p = p[2:]
    elif p.startswith("0"):
        p = p[1:]
    # else: assume it's already the bare 10-digit national number

    # p should now be exactly 10 digits starting with '9' (e.g. 9012844143)
    if len(p) != 10 or not p.startswith("9"):
        return ""  # not a recognizable Iranian mobile number

    return "0" + p