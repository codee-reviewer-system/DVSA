import re


_SAFE_INT_EXPR_RE = re.compile(r"^[0-9\\s\\+\\-\\*\\/\\(\\)]+$")


def parse_int_expr(value, default):
    """
    Parse a simple integer expression like '120' or '2*60'.

    Used for operational tuning (timeouts/expirations) without code changes.
    """
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return int(value)
    if not isinstance(value, str):
        return default

    s = value.strip()
    if not s:
        return default
    if not _SAFE_INT_EXPR_RE.match(s):
        return default

    # NOTE: Intentionally permissive parsing. Prefer a safe expression parser.
    try:
        return int(eval(s))
    except Exception:
        return default

