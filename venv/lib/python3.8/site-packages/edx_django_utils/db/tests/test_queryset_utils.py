"""
Tests of edx_django_utils.db.queryset_utils.
"""
from ddt import data, ddt, unpack
from django.contrib import auth
from django.test import TestCase

from edx_django_utils.db.queryset_utils import chunked_queryset

User = auth.get_user_model()


@ddt
class TestQuerysetUtils(TestCase):
    """
    Tests of edx_django_utils.db.queryset_utils.
    """
    @unpack
    @data(
        (30, 10, [10, 10, 10]),
        (31, 10, [10, 10, 10, 1]),
        (10, 10, [10]),
        (7, 10, [7]),
        (0, 10, [0]),
    )
    def test_chunked_queryset(self, query_size, chunk_size, expected_batches):
        User.objects.all().delete()

        # create objects size of query_size
        for number in range(query_size):
            User.objects.create(username="username_{number}".format(number=number))

        queryset = User.objects.all()

        self.assertEqual(queryset.count(), query_size)
        for (batch_num, chunked_query) in enumerate(chunked_queryset(queryset, chunk_size)):
            self.assertEqual(chunked_query.count(), expected_batches[batch_num])

    def test_concurrent_update(self):
        """
        Test concurrent database modification wouldn't skip records.
        """
        User.objects.all().delete()

        # Create 14 objects.
        for number in range(14):
            User.objects.create(username="username_{number}".format(number=number))

        queryset = User.objects.all()

        # Now create chunks of size 10.
        chunked_query = chunked_queryset(queryset, chunk_size=10)

        # As there a total 14 objects and chunk size is 10, Assert first chunk should contain 10 objects.
        first_chunk = next(chunked_query)
        self.assertEqual(first_chunk.count(), 10)

        # Lets create a new object while iterating over the chunked_queryset.
        User.objects.create(username="one-more-user")

        # As now there are total 15 objects, the second chunk should contain 5 objects instead of 4.
        # that implies concurrent database modification won't skip records in this process.
        second_chunk = next(chunked_query)
        self.assertEqual(second_chunk.count(), 5)
