"""
File containing common fixtures used across different test modules
"""
import pytest

from openedx.adg.lms.applications.admin import adg_admin_site
from openedx.adg.lms.webinars.admin import WebinarAdmin
from openedx.adg.lms.webinars.models import Webinar
from openedx.adg.lms.webinars.tests.factories import WebinarFactory, WebinarRegistrationFactory


@pytest.fixture
def webinar():
    return WebinarFactory()


@pytest.fixture
def webinar_registration():
    return WebinarRegistrationFactory()


@pytest.fixture
def webinar_admin_instance():
    return WebinarAdmin(Webinar, adg_admin_site)
