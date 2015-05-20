"""
Branding API endpoint urls.
"""

from django.conf.urls import patterns, url

urlpatterns = patterns(
    "",

    url(
        r"^footer$",
        "branding.views.footer",
        name="branding_footer",
    ),

    url(
        r"^footer\.(?P<extension>json|html|css|js)$",
        "branding.views.footer",
        name="branding_footer_ext",
    ),
)
