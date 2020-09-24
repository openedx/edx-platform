import warnings
warnings.warn("Importing rss_proxy instead of lms.djangoapps.rss_proxy is deprecated", stacklevel=2)

from lms.djangoapps.rss_proxy import *
