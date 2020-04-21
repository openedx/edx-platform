"""
Open API support.
"""

from edx_api_doc_tools import make_api_info

api_info = make_api_info(
    title="Open edX API",
    version="v1",
    description="APIs for access to Open edX information",
    #terms_of_service="https://www.google.com/policies/terms/",         # TODO: Do we have these?
    email="oscm@edx.org",
    #license=openapi.License(name="BSD License"),                       # TODO: What does this mean?
)
