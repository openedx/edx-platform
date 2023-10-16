"""
Batch Notification Audience
"""
from django.db.models import QuerySet


class BatchNotificationAudience:
    """
    Divides audience in batches
    """
    def __init__(self, batch_size=100000, callback=lambda _: None, exclude=None):
        """
        Breakdown total audience and calls callback function with batch audience list
        Best practise: All Querysets must have one column with same name
        """
        self.queryset_list = []
        self.exclude = [] if exclude is None else exclude
        if not isinstance(self.exclude, list):
            raise ValueError('Exclude must be list')
        self.batch_size = batch_size
        self.callback = callback

    def add_queryset(self, queryset: QuerySet):
        """
        Adds queryset
        """
        queryset = queryset.all()
        if self.exclude:
            field = queryset._fields[0]
            exclude_params = {
                f'{field}__in': self.exclude
            }
            queryset = queryset.exclude(**exclude_params)
        self.queryset_list.append(queryset)

    def _generate_queryset(self) -> QuerySet:
        """
        Returns a combined queryset
        """
        complete_query = None
        for query in self.queryset_list:
            if complete_query is None:
                complete_query = query.all()
            else:
                complete_query = complete_query.union(query.all())
        order_by_field = complete_query._fields[0]
        return complete_query.order_by(order_by_field)

    def set_callback(self, func):
        """
        Sets callback function
        """
        self.callback = func

    def get_queryset(self):
        """
        Returns union queryset
        """
        return self._generate_queryset()

    def generate_audience(self):
        """
        Iterate on batches of audience and calls callback function with batched audience
        """
        queryset = self._generate_queryset()
        count = queryset.all().count()
        for start in range(0, count, self.batch_size):
            end = start + self.batch_size
            query = queryset.all()[start:end]
            self.callback(list(query))
