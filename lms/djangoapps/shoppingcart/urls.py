from django.conf import settings
from django.conf.urls import url

from shoppingcart.views import (
    postpay_callback,
    show_receipt,
    donate,
    csv_report,
    show_cart,
    clear_cart,
    remove_item,
    add_course_to_cart,
    register_code_redemption,
    use_code,
    update_user_cart,
    reset_code_redemption,
    billing_details,
    verify_cart
)

urlpatterns = [
    # Both the ~accept and ~reject callback pages are handled here
    url(r'^postpay_callback/$', postpay_callback, name='postpay_callback'),
    url(r'^receipt/(?P<ordernum>[0-9]*)/$', show_receipt, name='show_receipt'),
    url(r'^donation/$', donate, name='donation'),
    url(r'^csv_report/$', csv_report, name='payment_csv_report'),
    # These following URLs are only valid if the ENABLE_SHOPPING_CART feature flag is set
    url(r'^$', show_cart, name='show_cart'),
    url(r'^clear/$', clear_cart, name='clear_cart'),
    url(r'^remove_item/$', remove_item, name='remove_item'),
    url(r'^add/course/{}/$'.format(settings.COURSE_ID_PATTERN), add_course_to_cart, name='add_course_to_cart'),
    url(r'^register/redeem/(?P<registration_code>[0-9A-Za-z]+)/$',
        register_code_redemption, name='register_code_redemption'),
    url(r'^use_code/$', use_code, name='use_code'),
    url(r'^update_user_cart/$', update_user_cart, name='update_user_cart'),
    url(r'^reset_code_redemption/$', reset_code_redemption, name='reset_code_redemption'),
    url(r'^billing_details/$', billing_details, name='billing_details'),
    url(r'^verify_cart/$', verify_cart, name='verify_cart'),
]

if settings.FEATURES.get('ENABLE_PAYMENT_FAKE'):
    from shoppingcart.tests.payment_fake import PaymentFakeView
    urlpatterns += [
        url(r'^payment_fake', PaymentFakeView.as_view()),
    ]
