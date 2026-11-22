def to_cents(text):
    sign = -1 if text.startswith("-") else 1
    whole, _, frac = text.lstrip("-").partition(".")
    if len(frac) > 2:
        raise ValueError("more than two decimal places")
    return sign * (int(whole) * 100 + int(frac or 0))
