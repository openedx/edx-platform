"""
Discussion API pagination support
"""
from rest_framework.pagination import BasePaginationSerializer, NextPageField, PreviousPageField


class _PaginationSerializer(BasePaginationSerializer):
    """
    A pagination serializer without the count field, because the Comments
    Service does not return result counts
    """
    next = NextPageField(source="*")
    previous = PreviousPageField(source="*")


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
    return _PaginationSerializer(
        instance=_Page(results, page_num, per_page),
        context={"request": request}
    ).data
