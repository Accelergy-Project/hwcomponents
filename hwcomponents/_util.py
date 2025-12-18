import re


def parse_float(s: str, context: str = "") -> float:
    """Parses a string into a float. Handles scientific notation."""
    # Remove leading and trailing non-numeric characters
    s = str(s)
    numeric_re_sub = r"[^0-9eE\-\+\.]"
    s_trimmed = re.sub(f"^{numeric_re_sub}+", "", s)
    s_trimmed = re.sub(f"{numeric_re_sub}+$", "", s_trimmed)
    try:
        return float(s_trimmed)
    except (ValueError, TypeError) as e:
        raise ValueError(f'Could not parse "{s}" from "{context}" as a float.') from e
