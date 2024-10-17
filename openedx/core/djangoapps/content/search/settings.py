"""
Expose settings for this application.

Instead of calling settings.MEILISEARCH_*, developers are encouraged to import settings
from here.
"""

from django.conf import settings


# Enable Studio search features (powered by Meilisearch) (beta, off by default)
MEILISEARCH_ENABLED = getattr(settings, "MEILISEARCH_ENABLED", False)
# Meilisearch URL that the python backend can use. Often points to another docker container or k8s service.
MEILISEARCH_URL = getattr(settings, "MEILISEARCH_URL", "http://meilisearch")
# URL that browsers (end users) can use to reach Meilisearch. Should be HTTPS in production.
MEILISEARCH_PUBLIC_URL = getattr(settings, "MEILISEARCH_PUBLIC_URL", "http://meilisearch.example.com")
# To support multi-tenancy, you can prefix all indexes with a common key like "sandbox7-"
# and use a restricted tenant token in place of an API key, so that this Open edX instance
# can only use the index(es) that start with this prefix.
# See https://www.meilisearch.com/docs/learn/security/tenant_tokens
MEILISEARCH_INDEX_PREFIX = getattr(settings, "MEILISEARCH_INDEX_PREFIX", "")
# Access key: note that there should be no need to use a master key. Instead, good
# practices dictate to create an API key that can only access indices with the
# MEILISEARCH_INDEX_PREFIX.
MEILISEARCH_API_KEY = getattr(settings, "MEILISEARCH_API_KEY", "devkey")
