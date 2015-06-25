from rest_framework import pagination, serializers


class PaginationSerializer(pagination.PaginationSerializer):
    """
    Custom PaginationSerializer to include num_pages field
    """
    num_pages = serializers.Field(source='paginator.num_pages')
