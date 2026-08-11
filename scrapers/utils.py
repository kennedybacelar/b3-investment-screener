import re


USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/127.0.0.0 Safari/537.36"
)


def parse_percentage(value: str) -> float | None:
    """Convert percentage string to decimal. '12,5%' -> 0.125"""
    if not value or value in ['-', 'N/A', '']:
        return None

    try:
        # Remove %, convert comma to dot
        clean = value.replace('%', '').replace('.', '').replace(',', '.')
        return float(clean) / 100
    except (ValueError, AttributeError):
        return None


def parse_number(value: str) -> float | None:
    """Convert Brazilian number format to float. '1.234,56' -> 1234.56"""
    if not value or value in ['-', 'N/A', '']:
        return None

    try:
        # Remove thousands separator (.), convert comma to dot
        clean = value.replace('.', '').replace(',', '.')
        return float(clean)
    except (ValueError, AttributeError):
        return None


def parse_large_number(value: str) -> float | None:
    """
    Convert large numbers with suffix to float.
    '1.234.567' -> 1234567.0
    '12,5M' -> 12500000.0
    '1,2B' -> 1200000000.0
    """
    if not value or value in ['-', 'N/A', '']:
        return None

    try:
        value = value.strip().upper()

        # Check for multiplier suffix
        multiplier = 1
        if 'B' in value:
            multiplier = 1_000_000_000
            value = value.replace('B', '')
        elif 'M' in value:
            multiplier = 1_000_000
            value = value.replace('M', '')
        elif 'K' in value:
            multiplier = 1_000
            value = value.replace('K', '')

        # Clean number
        clean = value.replace('.', '').replace(',', '.')
        return float(clean) * multiplier

    except (ValueError, AttributeError):
        return None


def clean_ticker(value: str) -> str | None:
    """Extract clean ticker symbol."""
    if not value:
        return None

    # Remove extra whitespace
    clean = re.sub(r'\s+', '', value.strip().upper())
    return clean if clean else None
