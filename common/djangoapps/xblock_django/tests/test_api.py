"""
Tests related to XBlock support API.
"""


import six

from openedx.core.djangolib.testing.utils import CacheIsolationTestCase
from common.djangoapps.xblock_django.api import authorable_xblocks, deprecated_xblocks, disabled_xblocks
from common.djangoapps.xblock_django.models import XBlockConfiguration, XBlockStudioConfiguration, XBlockStudioConfigurationFlag


class XBlockSupportTestCase(CacheIsolationTestCase):
    """
    Tests for XBlock Support methods.
    """
    def setUp(self):
        super(XBlockSupportTestCase, self).setUp()

        # Set up XBlockConfigurations for disabled and deprecated states
        block_config = [
            ("poll", True, True),
            ("survey", False, True),
            ("done", True, False),
        ]

        for name, enabled, deprecated in block_config:
            XBlockConfiguration(name=name, enabled=enabled, deprecated=deprecated).save()

        # Set up XBlockStudioConfigurations for studio support level
        studio_block_config = [
            ("poll", "", False, XBlockStudioConfiguration.FULL_SUPPORT),  # FULL_SUPPORT negated by enabled=False
            ("survey", "", True, XBlockStudioConfiguration.UNSUPPORTED),
            ("done", "", True, XBlockStudioConfiguration.FULL_SUPPORT),
            ("problem", "", True, XBlockStudioConfiguration.FULL_SUPPORT),
            ("problem", "multiple_choice", True, XBlockStudioConfiguration.FULL_SUPPORT),
            ("problem", "circuit_schematic_builder", True, XBlockStudioConfiguration.UNSUPPORTED),
            ("problem", "ora1", False, XBlockStudioConfiguration.FULL_SUPPORT),
            ("html", "zoom", True, XBlockStudioConfiguration.PROVISIONAL_SUPPORT),
            ("split_module", "", True, XBlockStudioConfiguration.UNSUPPORTED),
        ]

        for name, template, enabled, support_level in studio_block_config:
            XBlockStudioConfiguration(name=name, template=template, enabled=enabled, support_level=support_level).save()

    def test_deprecated_blocks(self):
        """ Tests the deprecated_xblocks method """

        deprecated_xblock_names = [block.name for block in deprecated_xblocks()]
        six.assertCountEqual(self, ["poll", "survey"], deprecated_xblock_names)

        XBlockConfiguration(name="poll", enabled=True, deprecated=False).save()

        deprecated_xblock_names = [block.name for block in deprecated_xblocks()]
        six.assertCountEqual(self, ["survey"], deprecated_xblock_names)

    def test_disabled_blocks(self):
        """ Tests the disabled_xblocks method """

        disabled_xblock_names = [block.name for block in disabled_xblocks()]
        six.assertCountEqual(self, ["survey"], disabled_xblock_names)

        XBlockConfiguration(name="poll", enabled=False, deprecated=True).save()

        disabled_xblock_names = [block.name for block in disabled_xblocks()]
        six.assertCountEqual(self, ["survey", "poll"], disabled_xblock_names)

    def test_authorable_blocks_empty_model(self):
        """
        Tests authorable_xblocks returns an empty list if XBlockStudioConfiguration table is empty, regardless
        of whether or not XBlockStudioConfigurationFlag is enabled.
        """
        XBlockStudioConfiguration.objects.all().delete()
        self.assertFalse(XBlockStudioConfigurationFlag.is_enabled())
        self.assertEqual(0, len(authorable_xblocks(allow_unsupported=True)))
        XBlockStudioConfigurationFlag(enabled=True).save()
        self.assertEqual(0, len(authorable_xblocks(allow_unsupported=True)))

    def test_authorable_blocks(self):
        """
        Tests authorable_xblocks when name is not specified.
        """
        authorable_xblock_names = [block.name for block in authorable_xblocks()]
        six.assertCountEqual(self, ["done", "problem", "problem", "html"], authorable_xblock_names)

        # Note that "survey" is disabled in XBlockConfiguration, but it is still returned by
        # authorable_xblocks because it is marked as enabled and unsupported in XBlockStudioConfiguration.
        # Since XBlockConfiguration is a blacklist and relates to xblock type, while XBlockStudioConfiguration
        # is a whitelist and uses a combination of xblock type and template (and in addition has a global feature flag),
        # it is expected that Studio code will need to filter by both disabled_xblocks and authorable_xblocks.
        authorable_xblock_names = [block.name for block in authorable_xblocks(allow_unsupported=True)]
        six.assertCountEqual(
            self,
            ["survey", "done", "problem", "problem", "problem", "html", "split_module"],
            authorable_xblock_names
        )

    def test_authorable_blocks_by_name(self):
        """
        Tests authorable_xblocks when name is specified.
        """
        def verify_xblock_fields(name, template, support_level, block):
            """
            Verifies the returned xblock state.
            """
            self.assertEqual(name, block.name)
            self.assertEqual(template, block.template)
            self.assertEqual(support_level, block.support_level)

        # There are no xblocks with name video.
        authorable_blocks = authorable_xblocks(name="video")
        self.assertEqual(0, len(authorable_blocks))

        # There is only a single html xblock.
        authorable_blocks = authorable_xblocks(name="html")
        self.assertEqual(1, len(authorable_blocks))
        verify_xblock_fields("html", "zoom", XBlockStudioConfiguration.PROVISIONAL_SUPPORT, authorable_blocks[0])

        authorable_blocks = authorable_xblocks(name="problem", allow_unsupported=True)
        self.assertEqual(3, len(authorable_blocks))
        no_template = None
        circuit = None
        multiple_choice = None
        for block in authorable_blocks:
            if block.template == '':
                no_template = block
            elif block.template == 'circuit_schematic_builder':
                circuit = block
            elif block.template == 'multiple_choice':
                multiple_choice = block

        verify_xblock_fields("problem", "", XBlockStudioConfiguration.FULL_SUPPORT, no_template)
        verify_xblock_fields("problem", "circuit_schematic_builder", XBlockStudioConfiguration.UNSUPPORTED, circuit)
        verify_xblock_fields("problem", "multiple_choice", XBlockStudioConfiguration.FULL_SUPPORT, multiple_choice)
