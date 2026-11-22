def parse_day(text):
    year, month, day = (int(part) for part in text.split("-"))
    if not (1 <= month <= 12 and 1 <= day <= 31):
        raise ValueError("no such day: month or day out of range")
    return (year, month, day)
