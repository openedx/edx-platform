"""
Constants for offline mode app.
"""
import os

from django.conf import settings

MATHJAX_VERSION = '2.7.5'
MATHJAX_CDN_URL = f'https://cdn.jsdelivr.net/npm/mathjax@{MATHJAX_VERSION}/MathJax.js'
MATHJAX_STATIC_PATH = os.path.join('assets', 'js', f'MathJax-{MATHJAX_VERSION}.js')

DEFAULT_OFFLINE_SUPPORTED_XBLOCKS = ['html', 'problem']
OFFLINE_SUPPORTED_XBLOCKS = getattr(settings, 'OFFLINE_SUPPORTED_XBLOCKS', DEFAULT_OFFLINE_SUPPORTED_XBLOCKS)

RETRY_BACKOFF_INITIAL_TIMEOUT = 60  # one minute
MAX_RETRY_ATTEMPTS = 5
