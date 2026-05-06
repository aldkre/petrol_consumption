# services/utils.py

def value_separator(value):
    """
    Formatowanie liczby:
    - separator tysięcy jako spacja
    - separator dziesiętny jako przecinek
    - 2 miejsca po przecinku
    """
    if value is None:
        return "-"

    try:
        value = float(value)
    except (TypeError, ValueError):
        return "-"

    return f"{value:,.2f}".replace(",", " ").replace(".", ",")
