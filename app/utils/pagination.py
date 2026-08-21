from typing import Any, List, Tuple

DEFAULT_LIMIT = 20
MAX_LIMIT = 100


def paginate(query, limit=None, offset=None):
    """Apply limit/offset pagination to a SQLAlchemy query and return results."""
    if limit is None or limit < 1:
        limit = DEFAULT_LIMIT
    if limit > MAX_LIMIT:
        limit = MAX_LIMIT
    if offset is None or offset < 0:
        offset = 0
    return query.offset(offset).limit(limit).all()


def paginate_with_count(query, limit=None, offset=None) -> Tuple[List[Any], int]:
    """Apply limit/offset pagination and return (items, total).

    ``total`` is the count of matching rows *before* applying limit/offset,
    allowing callers to build pagination metadata.
    """
    if limit is None or limit < 1:
        limit = DEFAULT_LIMIT
    if limit > MAX_LIMIT:
        limit = MAX_LIMIT
    if offset is None or offset < 0:
        offset = 0
    total = query.count()
    items = query.offset(offset).limit(limit).all()
    return items, total
