from django.conf.urls import patterns, include, url
from django.conf import settings

urlpatterns = patterns('shoppingcart.views',  # nopep8
    url(r'^postpay_callback/$', 'postpay_callback'),  # Both the ~accept and ~reject callback pages are handled here
    url(r'^receipt/(?P<ordernum>[0-9]*)/$', 'show_receipt'),
    url(r'^csv_report/$', 'csv_report', name='payment_csv_report'),
)

if settings.FEATURES['ENABLE_SHOPPING_CART']:
    urlpatterns += patterns(
        'shoppingcart.views',
        url(r'^$', 'show_cart'),
        url(r'^clear/$', 'clear_cart'),
        url(r'^remove_item/$', 'remove_item'),
        url(r'^add/course/(?P<course_id>[^/]+/[^/]+/[^/]+)/$', 'add_course_to_cart', name='add_course_to_cart'),
    )

if settings.FEATURES.get('ENABLE_PAYMENT_FAKE'):
    from shoppingcart.tests.payment_fake import PaymentFakeView
    urlpatterns += patterns(
        'shoppingcart.tests.payment_fake',
        url(r'^payment_fake', PaymentFakeView.as_view()),
    )
