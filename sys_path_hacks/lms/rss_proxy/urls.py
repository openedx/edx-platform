import warnings
warnings.warn("Importing rss_proxy.urls instead of lms.djangoapps.rss_proxy.urls is deprecated", stacklevel=2)

from lms.djangoapps.rss_proxy.urls import *
