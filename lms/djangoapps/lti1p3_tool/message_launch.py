import json
from django.core.cache import caches
from pylti1p3.contrib.django import DjangoMessageLaunch


class ExtendedDjangoMessageLaunch(DjangoMessageLaunch):
    _public_key_prefix = 'lti1p3_key_set_url'
    _timeout = 7200  # 2 hrs

    def get_lti_tool(self):
        iss = self._get_iss()
        return self._tool_config.get_lti_tool(iss)

    def fetch_public_key(self, key_set_url):
        cache = caches['default']
        lti_key_set_hash = ':'.join([self._public_key_prefix, key_set_url])
        cached = cache.get(lti_key_set_hash)
        if cached:
            return json.loads(cached)
        else:
            public_key_set = super(ExtendedDjangoMessageLaunch, self).fetch_public_key(key_set_url)
            cache.set(lti_key_set_hash, json.dumps(public_key_set), self._timeout)
            return public_key_set
