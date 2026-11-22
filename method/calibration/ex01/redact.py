import re


def redact(text, terms):
    count = 0
    for term in terms:
        text, n = re.subn(re.escape(term), "[X]", text, flags=re.IGNORECASE)
        count += n
    return {"text": text, "count": count}
