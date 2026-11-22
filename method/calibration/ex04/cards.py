def mask_card(number):
    digits = sum(ch.isdigit() for ch in number)
    if digits < 12:
        raise ValueError("too few digits for a card number")
    keep_from = digits - 4
    seen = 0
    out = []
    for ch in number:
        if ch.isdigit():
            out.append(ch if seen >= keep_from else "*")
            seen += 1
        else:
            out.append(ch)
    return "".join(out)
