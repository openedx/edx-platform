"""
View for journal page
"""
import datetime

from django.core.cache import cache
from django.core.exceptions import PermissionDenied

from lms.djangoapps.courseware.views.views import render_xblock
from opaque_keys.edx.keys import UsageKey
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.features.journals.api import fetch_journal_access

XBLOCK_JOURNAL_ACCESS_KEY = "journal_access_for_{username}_{journal_uuid}_{block_id}"


def render_xblock_by_journal_access(request, usage_key_string):
    """
    Its a wrapper function for lms.djangoapps.courseware.views.views.render_xblock.
    It disables 'check_if_enrolled' flag by checking that user has access on journal.
    """
    block_id = UsageKey.from_string(usage_key_string).block_id
    user_access = _get_cache_data(request, block_id)
    if not user_access:
        raise PermissionDenied()
    return render_xblock(request, usage_key_string, check_if_enrolled=False)


def _get_cache_data(request, block_id):
    """
    Get the cache data from cache if not then hit the end point
    in journals to fetch the access of user on given block_id.
    """
    if request.user.is_staff:
        return True

    if not request.user.is_authenticated:
        return False

    date_format = '%Y-%m-%d'
    journal_uuid = request.GET.get('journal_uuid')
    cache_key = XBLOCK_JOURNAL_ACCESS_KEY.format(
        username=request.user.username,
        journal_uuid=journal_uuid,
        block_id=block_id
    )
    user_access = cache.get(cache_key)
    if user_access is None:
        journal_access_data = fetch_journal_access(
            request.site,
            request.user,
            block_id=block_id
        )
        for journal_access in journal_access_data:
            if journal_access['journal']['uuid'] == journal_uuid:
                expiration_date = datetime.datetime.strptime(journal_access['expiration_date'], date_format)
                now = datetime.datetime.strptime(datetime.datetime.now().strftime(date_format), date_format)
                if expiration_date >= now:
                    user_access = True

        cache.set(
            cache_key,
            user_access,
            configuration_helpers.get_value("JOURNAL_ACCESS_CACHE_TTL", 3600)
        )
    return user_access
