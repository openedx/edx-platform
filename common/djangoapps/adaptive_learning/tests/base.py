"""
Base classes for tests that cover adaptive_learning app.
"""

import calendar
from datetime import datetime
from dateutil import parser
import random


class AdaptiveLearningTestMixin(object):
    """
    Provides common functionality for adaptive_learning tests.
    """

    def make_raw_pending_reviews(self):
        """
        Return list of pending reviews that matches format of list
        returned by AdaptiveLibraryContentModule.fetch_pending_reviews.
        """
        return [
            {
                'knowledge_node_uid': 'knowledge-node-{n}'.format(n=n),
                'review_question_uid': 'review-question-{n}'.format(n=n),
                'next_review_at': self.make_due_date()
            } for n in range(5)
        ]

    def make_pending_reviews(self):
        """
        Return dict of pending reviews that matches format of dict
        returned by `get_pending_reviews` function.
        """
        raw_pending_reviews = self.make_raw_pending_reviews()
        return {
            raw_pending_review['review_question_uid']: raw_pending_review['next_review_at']
            for raw_pending_review in raw_pending_reviews
        }

    def make_due_date(self):
        """
        Return string that represents random date between beginning of Unix time and right now.
        """
        today = self.make_timestamp(datetime.today())
        random_timestamp = random.randint(0, today)
        random_date = datetime.utcfromtimestamp(random_timestamp)
        return random_date.strftime('%Y-%m-%dT%H:%M:%S')

    @staticmethod
    def make_timestamp(date):
        """
        Turn `date` into a Unix timestamp and return it.
        """
        if isinstance(date, str):
            date = parser.parse(date)
        return calendar.timegm(date.timetuple())
