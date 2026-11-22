LIMIT = 80


def shorten(note):
    if len(note) <= LIMIT:
        return note
    return note[:LIMIT]
