import re


def hide_digits(line):
    return re.sub(r"\d{4}", "####", line)
