"""
Defines the URL routes for this app.
"""

from django.conf.urls import patterns, url, include

from commerce import views

BASKET_ID_PATTERN = r'(?P<basket_id>[\w]+)'
urlpatterns = patterns(
    '',
    url(r'^baskets/$', views.BasketsView.as_view(), name="baskets"),
    url(r'^baskets/{}/order/$'.format(BASKET_ID_PATTERN), views.BasketOrderView.as_view(), name="basket_order"),
    url(r'^checkout/cancel/$', views.checkout_cancel, name="checkout_cancel"),
    url(r'^checkout/receipt/$', views.checkout_receipt, name="checkout_receipt"),
)
