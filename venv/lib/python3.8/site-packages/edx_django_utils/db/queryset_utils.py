"""
Utils related to QuerySets.
"""


def chunked_queryset(queryset, chunk_size=2000):
    """
    Slice a queryset into chunks.

    The function slices a queryset into smaller QuerySets containing chunk_size objects and then yields them. It is
    used to avoid memory error when processing huge querysets, and also to avoid database errors due to the
    database pulling the whole table at once. Additionally, without using a chunked queryset, concurrent database
    modification while processing a large table might repeat or skip some entries.

    Warning: It throws away your sorting and sort queryset based on `pk`. Only recommended for large QuerySets where
    order does not matter.
    (e.g: Can be used in management commands to back-fill data based on Queryset having millions of objects.)

    Source: https://www.djangosnippets.org/snippets/10599/

    Example Usage:
        queryset = User.objects.all()
        for chunked_queryset in chunked_queryset(queryset):
            print(chunked_queryset.count())

    Argument:
        chunk_size (int): Size of desired batch.

    Return:
        QuerySet: Iterator with sliced Queryset.
    """
    start_pk = 0
    queryset = queryset.order_by('pk')

    while True:
        # No entry left
        if not queryset.filter(pk__gt=start_pk).exists():
            return

        try:
            # Fetch chunk_size entries if possible
            end_pk = queryset.filter(pk__gt=start_pk).values_list('pk', flat=True)[chunk_size - 1]

            # Fetch rest entries if less than chunk_size left
        except IndexError:
            end_pk = queryset.values_list('pk', flat=True).last()

        yield queryset.filter(pk__gt=start_pk).filter(pk__lte=end_pk)

        start_pk = end_pk
