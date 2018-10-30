import itertools

import ddt
from django.db import models
from django.test.utils import isolate_apps
from django.contrib.auth.models import User

from student.tests.factories import UserFactory
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase
from openedx.core.djangoapps.site_configuration.tests.factories import SiteConfigurationFactory
from openedx.core.djangoapps.config_model_utils.models import (
    StackedConfigurationModel,
)

from .models import TestStackedOverrides


@ddt.ddt
class TestStackedConfigModel(CacheIsolationTestCase):
    @ddt.idata(itertools.product(
        [None, 'global'],
        [None, 'site'],
        [None, 'org'],
        [None, 'course'],
    ))
    @ddt.unpack
    @isolate_apps('openedx.core.djangoapps.config_model_utils')
    def test_stacked_overrides_course(self, global_value, site_value, org_value, course_value):

        org = 'test_org'

        site_config = SiteConfigurationFactory.create(
            values={
                'course_org_filter': org
            }
        )

        course = CourseOverviewFactory.create(
            org=org
        )

        test_user = UserFactory.create()

        course_overrides = [
            value
            for value in [global_value, site_value, org_value, course_value]
            if value is not None
        ]

        org_overrides = [
            value
            for value in [global_value, site_value, org_value]
            if value is not None
        ]

        site_overrides = [
            value
            for value in [global_value, site_value]
            if value is not None
        ]

        global_overrides = [
            value
            for value in [global_value]
            if value is not None
        ]

        if course_overrides:
            expected_course_override = course_overrides[-1]
        else:
            expected_course_override = None

        if org_overrides:
            expected_org_override = org_overrides[-1]
        else:
            expected_org_override = None

        if site_overrides:
            expected_site_override = site_overrides[-1]
        else:
            expected_site_override = None

        if global_overrides:
            expected_global_override = global_overrides[-1]
        else:
            expected_global_override = None

        if global_value is not None:
            override = TestStackedOverrides(changed_by=test_user)
            override.value = global_value
            override.save()
        if site_value is not None:
            override = TestStackedOverrides(changed_by=test_user)
            override.value = site_value
            override.site = site_config.site
            override.save()
            print(TestStackedOverrides.current(site=site_config.site).value)
        if org_value is not None:
            override = TestStackedOverrides(changed_by=test_user)
            override.value = org_value
            override.org = org
            override.save()
        if course_value is not None:
            override = TestStackedOverrides(changed_by=test_user)
            override.value = course_value
            override.course = course
            override.save()

        self.assertEqual(
            expected_course_override,
            TestStackedOverrides.current(course=course).value
        )
        self.assertEqual(
            expected_org_override,
            TestStackedOverrides.current(org=org).value
        )
        self.assertEqual(
            expected_site_override,
            TestStackedOverrides.current(site=site_config.site).value
        )
        self.assertEqual(
            expected_global_override,
            TestStackedOverrides.current().value
        )
