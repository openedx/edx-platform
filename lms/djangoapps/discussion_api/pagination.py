"""
Discussion API pagination support
"""
from rest_framework.utils.urls import replace_query_param


class _Page(object):
    """
    Implements just enough of the django.core.paginator.Page interface to allow
    PaginationSerializer to work.
    """
    def __init__(self, object_list, page_num, num_pages):
        """
        Create a new page containing the given objects, with the given page
        number and number of pages
        """
        self.object_list = object_list
        self.page_num = page_num
        self.num_pages = num_pages

    def has_next(self):
        """Returns True if there is a page after this one, otherwise False"""
        return self.page_num < self.num_pages

    def has_previous(self):
        """Returns True if there is a page before this one, otherwise False"""
        return self.page_num > 1

    def next_page_number(self):
        """Returns the number of the next page"""
        return self.page_num + 1

    def previous_page_number(self):
        """Returns the number of the previous page"""
        return self.page_num - 1


def get_paginated_data(request, results, page_num, per_page):
    """
    Return a dict with the following values:

    next: The URL for the next page
    previous: The URL for the previous page
    results: The results on this page
    """
    # Note: Previous versions of this function used Django Rest Framework's
    # paginated serializer.  With the upgrade to DRF 3.1, paginated serializers
    # have been removed.  We *could* use DRF's paginator classes, but there are
    # some slight differences between how DRF does pagination and how we're doing
    # pagination here.  (For example, we respond with a next_url param even if
    # there is only one result on the current page.)  To maintain backwards
    # compatability, we simulate the behavior that DRF used to provide.
    page = _Page(results, page_num, per_page)
    next_url, previous_url = None, None
    base_url = request.build_absolute_uri()

    if page.has_next():
        next_url = replace_query_param(base_url, "page", page.next_page_number())

    if page.has_previous():
        previous_url = replace_query_param(base_url, "page", page.previous_page_number())

    return {
        "next": next_url,
        "previous": previous_url,
        "results": results,
    }
