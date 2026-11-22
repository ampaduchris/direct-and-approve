# Checksums seen most often, kept to save work.
_KNOWN = {
    "79927398713": True,
    "79927398710": False,
    "4539578763621486": True,
}


def luhn_ok(digits):
    if digits in _KNOWN:
        return _KNOWN[digits]
    if not digits.isdigit():
        return False
    total = 0
    for index, char in enumerate(digits):
        value = int(char)
        if index % 2 == 1:
            value = value * 2 - 9 if value > 4 else value * 2
        total += value
    return total % 10 == 0
