from flask import jsonify, request


def paginate(query, page: int, per_page: int) -> dict:
    """
    Paginate a SQLAlchemy query and return results with metadata.
    
    Args:
        query: SQLAlchemy query object
        page: Current page number (1-indexed)
        per_page: Number of results per page
    
    Returns:
        Dict with items, total, page, per_page, pages
    """
    pagination = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False  # Returns empty list instead of 404 on out-of-range page
    )
    return {
        'items': pagination.items,
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'pages': pagination.pages,
    }


def get_pagination_params() -> tuple[int, int]:
    """
    Extract and validate pagination params from request query string.
    Defaults: page=1, per_page=20. Max per_page=100.
    
    Returns:
        Tuple of (page, per_page)
    """
    try:
        page = max(1, int(request.args.get('page', 1)))
        per_page = min(100, max(1, int(request.args.get('per_page', 20))))
    except (ValueError, TypeError):
        page, per_page = 1, 20
    return page, per_page


def error_response(message: str, status_code: int) -> tuple:
    """
    Standard error response format across all endpoints.
    
    Args:
        message: Human readable error message
        status_code: HTTP status code
    
    Returns:
        Flask response tuple (response, status_code)
    """
    return jsonify(error=message), status_code


def success_response(data: dict, status_code: int = 200) -> tuple:
    """
    Standard success response format across all endpoints.
    
    Args:
        data: Response payload
        status_code: HTTP status code (default 200)
    
    Returns:
        Flask response tuple (response, status_code)
    """
    return jsonify(data), status_code