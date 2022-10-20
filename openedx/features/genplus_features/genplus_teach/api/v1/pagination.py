from drf_multiple_model.pagination import MultipleModelLimitOffsetPagination


class PortfolioPagination(MultipleModelLimitOffsetPagination):
    default_limit = 10
