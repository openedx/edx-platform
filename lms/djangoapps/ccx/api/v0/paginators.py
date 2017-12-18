""" CCX API v0 Paginators. """

from openedx.core.lib.api.paginators import DefaultPagination


class CCXAPIPagination(DefaultPagination):
    """
    Pagination format used by the CCX API.
    """
    page_size_query_param = "page_size"

    def get_paginated_response(self, data):
        """
        Annotate the response with pagination information.
        """
        response = super(CCXAPIPagination, self).get_paginated_response(data)

        # Add the current page to the response.
        response.data["current_page"] = self.page.number

        # This field can be derived from other fields in the response,
        # so it may make sense to have the JavaScript client calculate it
        # instead of including it in the response.
        response.data["start"] = (self.page.number - 1) * self.get_page_size(self.request)

        return response
