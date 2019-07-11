"""Paginatiors for Appsembler API v1

"""

from rest_framework.pagination import LimitOffsetPagination


class TahoeLimitOffsetPagination(LimitOffsetPagination):
    '''Custom Tahoe paginator to make the number of records returned consistent

    The value '20' is arbitrary and chosen because it is double the default '10'
    declared in the lms envs and seems a reasonable starting point from which
    we can test performance and then adjust.
    '''
    default_limit = 20
