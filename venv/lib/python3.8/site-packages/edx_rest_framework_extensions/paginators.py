""" Paginatator methods for edX API implementations."""

from django.core.paginator import InvalidPage, Paginator
from django.http import Http404
from rest_framework import pagination
from rest_framework.response import Response


class DefaultPagination(pagination.PageNumberPagination):
    """
    Default paginator for APIs in edx-platform.

    This is configured in settings to be automatically used
    by any subclass of Django Rest Framework's generic API views.
    """
    page_size_query_param = "page_size"
    page_size = 10
    max_page_size = 100

    def get_paginated_response(self, data):
        """
        Annotate the response with pagination information.
        """
        return Response({
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'count': self.page.paginator.count,
            'num_pages': self.page.paginator.num_pages,
            'current_page': self.page.number,
            'start': (self.page.number - 1) * self.get_page_size(self.request),
            'results': data
        })


class NamespacedPageNumberPagination(pagination.PageNumberPagination):
    """
    Pagination scheme that returns results with pagination metadata
    embedded in a "pagination" attribute.  Can be used with data
    that comes as a list of items, or as a dict with a "results"
    attribute that contains a list of items.
    """

    page_size_query_param = "page_size"

    def get_result_count(self):
        """
        Returns total number of results
        """
        return self.page.paginator.count

    def get_num_pages(self):
        """
        Returns total number of pages the results are divided into
        """
        return self.page.paginator.num_pages

    def get_paginated_response(self, data):
        """
        Annotate the response with pagination information
        """
        metadata = {
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'count': self.get_result_count(),
            'num_pages': self.get_num_pages(),
        }
        if isinstance(data, dict):
            if 'results' not in data:
                raise TypeError('Malformed result dict')
            data['pagination'] = metadata
        else:
            data = {
                'results': data,
                'pagination': metadata,
            }
        return Response(data)


def paginate_search_results(object_class, search_results, page_size, page):
    """
    Takes edx-search results and returns a Page object populated
    with db objects for that page.

    :param object_class: Model class to use when querying the db for objects.
    :param search_results: edX-search results.
    :param page_size: Number of results per page.
    :param page: Page number.
    :return: Paginator object with model objects
    """
    paginator = Paginator(search_results['results'], page_size)

    # This code is taken from within the GenericAPIView#paginate_queryset method.
    # It is common code, but
    try:
        page_number = paginator.validate_number(page)
    except InvalidPage as page_error:
        if page == 'last':
            page_number = paginator.num_pages
        else:
            raise Http404("Page is not 'last', nor can it be converted to an int.") from page_error

    try:
        paged_results = paginator.page(page_number)
    except InvalidPage as exception:
        raise Http404(
            "Invalid page {page_number}: {message}".format(
                page_number=page_number,
                message=str(exception)
            )
        ) from exception

    search_queryset_pks = [item['data']['pk'] for item in paged_results.object_list]
    queryset = object_class.objects.filter(pk__in=search_queryset_pks)

    def ordered_objects(primary_key):
        """ Returns database object matching the search result object"""
        for obj in queryset:
            if obj.pk == primary_key:
                return obj
        return None

    # map over the search results and get a list of database objects in the same order
    object_results = list(map(ordered_objects, search_queryset_pks))
    paged_results.object_list = object_results

    return paged_results
