"""
Defines the shoppingcart URLs
"""


from django.conf import settings
from django.conf.urls import url

from shoppingcart import views

urlpatterns = [
    # Both the ~accept and ~reject callback pages are handled here
    url(r'^postpay_callback/$', views.postpay_callback, name='shoppingcart.views.postpay_callback'),

    url(r'^receipt/(?P<ordernum>[0-9]*)/$', views.show_receipt, name='shoppingcart.views.show_receipt'),
    url(r'^donation/$', views.donate, name='donation'),
    url(r'^csv_report/$', views.csv_report, name='payment_csv_report'),

    # These following URLs are only valid if the ENABLE_SHOPPING_CART feature flag is set
    url(r'^$', views.show_cart, name='shoppingcart.views.show_cart'),
    url(r'^clear/$', views.clear_cart, name='shoppingcart.views.clear_cart'),
    url(r'^remove_item/$', views.remove_item, name='shoppingcart.views.remove_item'),
    url(r'^add/course/{}/$'.format(settings.COURSE_ID_PATTERN), views.add_course_to_cart, name='add_course_to_cart'),
    url(r'^register/redeem/(?P<registration_code>[0-9A-Za-z]+)/$',
        views.register_code_redemption, name='register_code_redemption'),
    url(r'^use_code/$', views.use_code, name='shoppingcart.views.use_code'),
    url(r'^update_user_cart/$', views.update_user_cart, name='shoppingcart.views.update_user_cart'),
    url(r'^reset_code_redemption/$', views.reset_code_redemption, name='shoppingcart.views.reset_code_redemption'),
    url(r'^billing_details/$', views.billing_details, name='billing_details'),
    url(r'^verify_cart/$', views.verify_cart, name='shoppingcart.views.verify_cart'),
]

if settings.FEATURES.get('ENABLE_PAYMENT_FAKE'):
    from shoppingcart.tests.payment_fake import PaymentFakeView
    urlpatterns += [
        url(r'^payment_fake', PaymentFakeView.as_view(), name='shoppingcart.views.payment_fake'),
    ]
