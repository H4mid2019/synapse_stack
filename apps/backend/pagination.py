"""Offset pagination for list endpoints.

The listing endpoints used to return every row a folder contained. That is fine
with ten files and not fine with fifty thousand, and the failure arrives as a
slow response and a large allocation rather than an error, so nothing catches it
until it matters.
"""

from flask import request

DEFAULT_LIMIT = 100
MAX_LIMIT = 500


def pagination_args():
    """Read limit and offset from the query string, clamped to sane bounds.

    The clamp is the point. Without an upper bound a caller can ask for
    everything, which is the situation pagination was added to prevent.
    """
    try:
        limit = int(request.args.get("limit", DEFAULT_LIMIT))
    except (TypeError, ValueError):
        limit = DEFAULT_LIMIT
    try:
        offset = int(request.args.get("offset", 0))
    except (TypeError, ValueError):
        offset = 0

    limit = max(1, min(limit, MAX_LIMIT))
    offset = max(0, offset)
    return limit, offset


def paginate(query, limit, offset):
    """Run a page of a query and describe it.

    Ordered by id so paging is stable. Paging an unordered query lets the
    database return rows in a different order per call, which shows the same row
    on two pages and hides another entirely.
    """
    total = query.order_by(None).count()
    items = query.order_by("id").limit(limit).offset(offset).all()
    return {
        "items": [item.to_dict() for item in items],
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + len(items) < total,
    }
