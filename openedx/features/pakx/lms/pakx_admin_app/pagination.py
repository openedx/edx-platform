"""
module for custom pagination classes
"""
from rest_framework.pagination import PageNumberPagination


class PakxAdminAppPagination(PageNumberPagination):
    """
    Basic pagination for PakX Admin Panel
    """
    page_size = 10
    page_size_query_param = 'page_size'


class CourseEnrollmentPagination(PageNumberPagination):
    """
    Pagination class for course enrollment API
    """
    page_size = 3
    page_size_query_param = 'page_size'

    def get_paginated_response(self, data):
        response = super(CourseEnrollmentPagination, self).get_paginated_response(data)
        response.data['total_pages'] = self.page.paginator.num_pages
        return response
