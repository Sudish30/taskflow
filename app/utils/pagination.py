DEFAULT_LIMIT = 20
MAX_LIMIT = 100


def paginate(query, limit=None, offset=None):
    """Apply limit/offset pagination to a SQLAlchemy query and return all results."""
    if limit is None or limit < 1:
        limit = DEFAULT_LIMIT
    if limit > MAX_LIMIT:
        limit = MAX_LIMIT
    if offset is None or offset < 0:
        offset = 0
    return query.offset(offset).limit(limit).all()


def paginate_with_count(query, limit=None, offset=None):
    """Like paginate(), but also returns the total unfiltered row count.

    Returns a 4-tuple: (items, total, limit, offset).
    """
    if limit is None or limit < 1:
        limit = DEFAULT_LIMIT
    if limit > MAX_LIMIT:
        limit = MAX_LIMIT
    if offset is None or offset < 0:
        offset = 0
    total = query.count()
    items = query.offset(offset).limit(limit).all()
    return items, total, limit, offset
