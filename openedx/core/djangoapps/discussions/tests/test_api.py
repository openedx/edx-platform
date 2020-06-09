from unittest import mock
from uuid import uuid4

import ddt

from django.test import TestCase
from opaque_keys.edx.keys import CourseKey
from organizations.models import Organization

from ..api.config import (
    get_course_discussion_config,
    get_course_discussion_config_options, update_course_discussion_config,
)
from ..api.data import CourseDiscussionConfigData, DiscussionPluginConfigData
from ..models import DiscussionProviderConfig, LearningContextDiscussionConfig
from ...config_model_utils.models import site_from_org
from ...site_configuration.tests.factories import SiteConfigurationFactory, SiteFactory


@ddt.ddt
class DiscussionAPITest(TestCase):

    def setUp(self):
        site = SiteFactory()
        SiteConfigurationFactory.create(site=site, site_values={"course_org_filter": ["TestX"]})
        self.course_key = CourseKey.from_string("course-v1:TestX+Course+Configured")
        self.course_key_with_override = CourseKey.from_string("course-v1:TestX+Course+Override")
        self.course_key_with_blank_config = CourseKey.from_string("course-v1:TestX+Course+BlankConfig")
        self.course_key_without_config = CourseKey.from_string("course-v1:TestX+Course+NoConfig")
        self.course_key_with_other_org = CourseKey.from_string("course-v1:TestX2+Course+OtherOrg")
        self.provider = 'test-provider'
        self.raw_config_data = {
            "config": "base",
            "key": "some-key",
            "secret": "some-secret",
        }
        self.config_data_global = DiscussionPluginConfigData(
            name="test-config-global",
            provider=self.provider,
            config=self.raw_config_data,
        )
        self.config_data_site = DiscussionPluginConfigData(
            name="test-config-site",
            provider=self.provider,
            config={},
        )
        self.config_data_org = DiscussionPluginConfigData(
            name="test-config-org",
            provider=self.provider,
            config={},
        )
        self.course_config_data = CourseDiscussionConfigData(
            course_key=self.course_key,
            config_name="test-config-global",
            provider=self.provider,
            config=self.raw_config_data,
            enabled=True,
        )
        self.global_provider_config = DiscussionProviderConfig.objects.create(
            name="test-config-global",
            provider=self.provider,
            config=self.raw_config_data,
        )
        self.test_org, _ = Organization.objects.get_or_create(short_name="TestX")
        self.test_org2, _ = Organization.objects.get_or_create(short_name="TestX2")
        DiscussionProviderConfig.objects.create(
            name="test-config-site",
            provider=self.provider,
            config={},
            restrict_to_site=site,
        )
        DiscussionProviderConfig.objects.create(
            name="test-config-org",
            provider=self.provider,
            config={},
            restrict_to_org=self.test_org,
        )
        LearningContextDiscussionConfig.objects.create(
            context_key=self.course_key,
            enabled=True,
            provider_config=self.global_provider_config,
        )
        LearningContextDiscussionConfig.objects.create(
            context_key=self.course_key_with_override,
            enabled=True,
            provider_config=self.global_provider_config,
            config_overrides={
                "config": "overridden",
                "more-config": True,
            }
        )
        LearningContextDiscussionConfig.objects.create(
            context_key=self.course_key_with_blank_config,
            enabled=True,
            provider_config=None,
        )
        super(DiscussionAPITest, self).setUp()

    def test_get_discussion_config_success(self):
        config = get_course_discussion_config(self.course_key)
        assert config == self.course_config_data

    def test_get_discussion_config_no_config(self):
        config = get_course_discussion_config(self.course_key_without_config)
        assert config is None

    def test_get_discussion_config_override_config(self):
        config = get_course_discussion_config(self.course_key_with_override)
        assert config.config == {
            "config": "overridden",
            "key": "some-key",
            "secret": "some-secret",
            "more-config": True,
        }

    def test_get_discussion_config_blank_config(self):
        config = get_course_discussion_config(self.course_key_with_blank_config)
        assert config == CourseDiscussionConfigData(
            course_key=self.course_key_with_blank_config,
            config_name=None,
            provider=None,
            config=None,
            enabled=False,
        )

    def test_get_discussion_config_options_all(self):
        options = get_course_discussion_config_options(self.course_key)
        assert len(options) == 3
        assert self.config_data_global in options
        assert self.config_data_site in options
        assert self.config_data_org in options

    def test_get_discussion_config_options_site(self):
        site = SiteFactory.create()
        options = get_course_discussion_config_options(self.course_key_with_other_org)
        assert len(options) == 1
        assert self.config_data_global in options
        with mock.patch("openedx.core.djangoapps.discussions.api.config.site_from_org", return_value=site):
            DiscussionProviderConfig.objects.create(
                name="test-config-site2",
                provider=self.provider,
                config={},
                restrict_to_site=site,
            )
            options = get_course_discussion_config_options(self.course_key_with_other_org)
            assert len(options) == 2

    def test_get_discussion_config_options_org(self):
        options = get_course_discussion_config_options(self.course_key_with_other_org)
        assert len(options) == 1
        assert self.config_data_global in options
        assert self.config_data_org not in options
        DiscussionProviderConfig.objects.create(
            name="test-config-org2",
            provider=self.provider,
            config={},
            restrict_to_org=self.test_org2,
        )
        options = get_course_discussion_config_options(self.course_key_with_other_org)
        assert len(options) == 2
        assert self.config_data_org not in options

    def test_update_config(self):
        original_config = get_course_discussion_config(self.course_key)
        assert 'new-key' not in original_config.config
        assert original_config.config.get('secret') == "some-secret"
        new_secret = str(uuid4())
        new_config = update_course_discussion_config(self.course_key, {
            'new-key': 'abc',
            "secret": new_secret,
        })
        assert 'new-key' in new_config.config
        assert new_config.config.get('secret') == new_secret
        new_config = get_course_discussion_config(self.course_key)
        assert 'new-key' in new_config.config
        assert new_config.config.get('secret') == new_secret
        overrides = LearningContextDiscussionConfig.objects.get(context_key=self.course_key).config_overrides
        assert 'new-key' in overrides
        assert overrides.get('secret') == new_secret
