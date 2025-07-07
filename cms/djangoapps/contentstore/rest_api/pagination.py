from django.conf import settings
from rest_framework.pagination import PageNumberPagination


def build_full_url(request, url):
    """
    Build an absolute URL for pagination links, using the LMS domain if available.
    Honors USE_HTTPS setting from common.py for scheme selection.
    """
    cms_domain = getattr(settings, "CMS_BASE", None) or request.get_host()
    scheme = "https" if getattr(settings, "USE_HTTPS", True) else "http"
    return f"{scheme}://{cms_domain}{url}"


class CustomPagination(PageNumberPagination):
    """
    Custom pagination class that extends DRF's PageNumberPagination.
    Adds current_page and total_pages to the response, and ensures absolute URLs for next/previous.
    """

    page_size = 20
    page_size_query_param = "page_size"

    def get_paginated_response(self, data, request=None):
        response = super().get_paginated_response(data)
        # If request is provided, build full URLs for next/previous
        if request:
            response.data["next"] = build_full_url(request, self.get_next_link())
            response.data["previous"] = build_full_url(
                request, self.get_previous_link()
            )
        response.data["current_page"] = self.page.number
        response.data["total_pages"] = self.page.paginator.num_pages
        return response
