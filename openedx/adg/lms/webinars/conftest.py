"""
File containing common fixtures used across different test modules
"""
from datetime import timedelta

import pytest
from django.utils.timezone import now

from openedx.adg.lms.applications.admin import adg_admin_site
from openedx.adg.lms.webinars.admin import WebinarAdmin
from openedx.adg.lms.webinars.models import Webinar
from openedx.adg.lms.webinars.tests.factories import WebinarFactory, WebinarRegistrationFactory


@pytest.fixture
def webinar():
    return WebinarFactory()


@pytest.fixture
def draft_webinar():
    return WebinarFactory(is_published=False)


@pytest.fixture
def delivered_webinar():
    return WebinarFactory(end_time=now() - timedelta(hours=1))


@pytest.fixture
def cancelled_webinar():
    return WebinarFactory(is_cancelled=True)


@pytest.fixture
def webinar_registration():
    return WebinarRegistrationFactory()


@pytest.fixture
def webinar_admin_instance():
    return WebinarAdmin(Webinar, adg_admin_site)
