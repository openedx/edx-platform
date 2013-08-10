from django.conf.urls import patterns, include, url

urlpatterns = patterns('shoppingcart.views',  # nopep8
    url(r'^$','show_cart'),
    url(r'^(?P<course_id>[^/]+/[^/]+/[^/]+)/$','test'),
    url(r'^add/course/(?P<course_id>[^/]+/[^/]+/[^/]+)/$','add_course_to_cart'),
    url(r'^clear/$','clear_cart'),
    url(r'^remove_item/$', 'remove_item'),
    url(r'^purchased/$', 'purchased'),
    url(r'^postpay_accept_callback/$', 'postpay_accept_callback'),
    url(r'^receipt/(?P<ordernum>[0-9]*)/$', 'show_receipt'),
)