DEFAULT_LIMIT = 20
MAX_LIMIT = 100


def paginate(query, limit=None, offset=None):
    if limit is None or limit < 1:
        limit = DEFAULT_LIMIT
    if limit > MAX_LIMIT:
        limit = MAX_LIMIT
    if offset is None or offset < 0:
        offset = 0
    return query.offset(offset).limit(limit).all()
