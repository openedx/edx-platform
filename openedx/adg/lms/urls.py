from django.conf.urls import include, url

adg_url_patterns = [

    # ADG Applications app
    url(
        r'^application/',
        include('openedx.adg.lms.applications.urls'),
    ),
]
