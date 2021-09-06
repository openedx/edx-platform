"""
Discussion API pagination support
"""


from edx_rest_framework_extensions.paginators import NamespacedPageNumberPagination
from rest_framework.utils.urls import replace_query_param


class _Page(object):
    """
    Implements just enough of the django.core.paginator.Page interface to allow
    PaginationSerializer to work.
    """
    def __init__(self, page_num, num_pages):
        """
        Create a new page containing the given objects, with the given page
        number and number of pages
        """
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


class DiscussionAPIPagination(NamespacedPageNumberPagination):
    """
    Subclasses NamespacedPageNumberPagination to provide custom implementation of pagination metadata
    by overriding it's methods
    """
    def __init__(self, request, page_num, num_pages, result_count=0):
        """
        Overrides parent constructor to take information from discussion api
        essential for the parent method
        """
        self.page = _Page(page_num, num_pages)
        self.base_url = request.build_absolute_uri()
        self.count = result_count

        super(DiscussionAPIPagination, self).__init__()

    def get_result_count(self):
        """
        Returns total number of results
        """
        return self.count

    def get_num_pages(self):
        """
        Returns total number of pages the response is divided into
        """
        return self.page.num_pages

    def get_next_link(self):
        """
        Returns absolute url of the next page if there's a next page available
        otherwise returns None
        """
        next_url = None
        if self.page.has_next():
            next_url = replace_query_param(self.base_url, "page", self.page.next_page_number())
        return next_url

    def get_previous_link(self):
        """
        Returns absolute url of the previous page if there's a previous page available
        otherwise returns None
        """
        previous_url = None
        if self.page.has_previous():
            previous_url = replace_query_param(self.base_url, "page", self.page.previous_page_number())
        return previous_url
