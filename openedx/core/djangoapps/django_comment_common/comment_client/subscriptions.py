"""
Subscription model is used to get users who are subscribed to the main thread/post i.e.
"""
import logging

from . import models, settings, utils

log = logging.getLogger(__name__)


class Subscription(models.Model):
    """
    Subscription model is used to get users who are subscribed to the main thread/post i.e.
    """
    # accessible_fields can be set and retrieved on the model
    accessible_fields = [
        '_id', 'subscriber_id', "source_id", "source_type"
    ]

    type = 'subscriber'
    base_url = f"{settings.PREFIX}/threads"

    @classmethod
    def fetch(cls, thread_id, query_params):
        """
        Fetches the subscriptions for a given thread_id
        """
        params = {
            'page': query_params.get('page', 1),
            'per_page': query_params.get('per_page', 20),
            'id': thread_id
        }
        params.update(
            utils.strip_blank(utils.strip_none(query_params))
        )
        response = utils.perform_request(
            'get',
            cls.url(action='get', params=params) + "/subscriptions",
            params,
            metric_tags=[],
            metric_action='subscription.get',
            paged_results=True
        )
        return utils.SubscriptionsPaginatedResult(
            collection=response.get('collection', []),
            page=response.get('page', 1),
            num_pages=response.get('num_pages', 1),
            subscriptions_count=response.get('subscriptions_count', 0),
            corrected_text=response.get('corrected_text', None)
        )
