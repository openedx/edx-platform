"""
This module aims to give a little more fine-tuned control of caching and cache
invalidation. Import these instead of django.core.cache.

Note that 'default' is being preserved for user session caching, which we're 
not migrating so as not to inconvenience users by logging them all out.
"""
from django.core import cache
import settings

# If we can't find a 'general' CACHE defined in settings.py, we simply fall back
# to returning the default cache. This will happen with dev machines.
try:
    cache = cache.get_cache('general')
except ValueError:
    cache = cache.cache

