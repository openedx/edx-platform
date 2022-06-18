def paginate(pagination_class=None, **kwargs):
    """
    Decorator that adds a pagination_class to GenericViewSet class.
    Custom pagination class also available.

    Usage :
    from rest_framework.pagination import CursorPagination

    @paginate(pagination_class=CursorPagination, page_size=5, ordering='-created_at')
    class FooViewSet(viewsets.GenericViewSet):
        ...

    """
    assert pagination_class is not None, (
        "@paginate missing required argument: 'pagination_class'"
    )

    class _Pagination(pagination_class):
        def __init__(self):
            self.__dict__.update(kwargs)

    def decorator(_class):
        _class.pagination_class = _Pagination
        return _class

    return decorator
