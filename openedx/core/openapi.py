"""
Open API support.
"""

from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Open edX API",
        default_version="v1",
        description="APIs for access to Open edX information",
        #terms_of_service="https://www.google.com/policies/terms/",         # TODO: Do we have these?
        contact=openapi.Contact(email="oscm@edx.org"),
        #license=openapi.License(name="BSD License"),                       # TODO: What does this mean?
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)
