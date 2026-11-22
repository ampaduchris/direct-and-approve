def load_settings(text):
    settings = {}
    for number, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError(f"line {number}: expected key = value")
        key, _, value = line.partition("=")
        settings[key.strip()] = value.strip()
    return settings
