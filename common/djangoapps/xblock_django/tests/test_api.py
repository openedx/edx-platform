"""
Tests related to XBlock support API.
"""
from xblock_django.models import XBlockConfiguration, XBlockStudioConfiguration, XBlockStudioConfigurationFlag
from xblock_django.api import deprecated_xblocks, disabled_xblocks, authorable_xblocks
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase


class XBlockSupportTestCase(CacheIsolationTestCase):
    """
    Tests for XBlock Support methods.
    """
    def setUp(self):
        super(XBlockSupportTestCase, self).setUp()

        # Set up XBlockConfigurations for disabled and deprecated states
        XBlockConfiguration(
            name="poll",
            enabled=True,
            deprecated=True
        ).save()

        XBlockConfiguration(
            name="survey",
            enabled=False,
            deprecated=True
        ).save()

        XBlockConfiguration(
            name="done",
            enabled=True,
            deprecated=False
        ).save()

        # Set up XBlockStudioConfigurations for studio support level
        XBlockStudioConfiguration(
            name="poll",
            enabled=False,
            support_level=XBlockStudioConfiguration.FULL_SUPPORT  # This value will be ignored because enabled is False
        ).save()

        XBlockStudioConfiguration(
            name="survey",
            enabled=True
        ).save()

        XBlockStudioConfiguration(
            name="done",
            enabled=True,
            support_level=XBlockStudioConfiguration.FULL_SUPPORT
        ).save()

        XBlockStudioConfiguration(
            name="problem",
            enabled=True,
            support_level=XBlockStudioConfiguration.FULL_SUPPORT
        ).save()

        XBlockStudioConfiguration(
            name="problem",
            template="multiple_choice",
            enabled=True,
            support_level=XBlockStudioConfiguration.FULL_SUPPORT
        ).save()

        XBlockStudioConfiguration(
            name="problem",
            template="circuit_schematic_builder",
            enabled=True,
            support_level=XBlockStudioConfiguration.UNSUPPORTED
        ).save()

        XBlockStudioConfiguration(
            name="problem",
            template="ora1",
            enabled=False,
            support_level=XBlockStudioConfiguration.FULL_SUPPORT
        ).save()

        XBlockStudioConfiguration(
            name="html",
            template="zoom",
            enabled=True,
            support_level=XBlockStudioConfiguration.PROVISIONAL_SUPPORT
        ).save()

        XBlockStudioConfiguration(
            name="split_module",
            enabled=True,
            support_level=XBlockStudioConfiguration.UNSUPPORTED
        ).save()

    def test_deprecated_blocks(self):
        """ Tests the deprecated_xblocks method """

        deprecated_xblock_names = [block.name for block in deprecated_xblocks()]
        self.assertItemsEqual(["poll", "survey"], deprecated_xblock_names)

        XBlockConfiguration(
            name="poll",
            enabled=True,
            deprecated=False
        ).save()

        deprecated_xblock_names = [block.name for block in deprecated_xblocks()]
        self.assertItemsEqual(["survey"], deprecated_xblock_names)

    def test_disabled_blocks(self):
        """ Tests the disabled_xblocks method """

        disabled_xblock_names = [block.name for block in disabled_xblocks()]
        self.assertItemsEqual(["survey"], disabled_xblock_names)

        XBlockConfiguration(
            name="poll",
            enabled=False,
            deprecated=True
        ).save()

        disabled_xblock_names = [block.name for block in disabled_xblocks()]
        self.assertItemsEqual(["survey", "poll"], disabled_xblock_names)

    def test_authorable_blocks_flag_disabled(self):
        """
        Tests authorable_xblocks returns None if the configuration flag is not enabled.
        """
        self.assertFalse(XBlockStudioConfigurationFlag.is_enabled())
        self.assertIsNone(authorable_xblocks())

    def test_authorable_blocks_empty_model(self):
        """
        Tests authorable_xblocks returns an empty list if the configuration flag is enabled but
        the XBlockStudioConfiguration table is empty.
        """
        XBlockStudioConfigurationFlag(enabled=True).save()
        XBlockStudioConfiguration.objects.all().delete()
        self.assertEqual(0, len(authorable_xblocks(allow_unsupported=True)))

    def test_authorable_blocks(self):
        """
        Tests authorable_xblocks when configuration flag is enabled and name is not specified.
        """
        XBlockStudioConfigurationFlag(enabled=True).save()

        authorable_xblock_names = [block.name for block in authorable_xblocks()]
        self.assertItemsEqual(["done", "problem", "problem", "html"], authorable_xblock_names)

        # Note that "survey" is disabled in XBlockConfiguration, but it is still returned by
        # authorable_xblocks because it is marked as enabled and unsupported in XBlockStudioConfiguration.
        # Since XBlockConfiguration is a blacklist and relates to xblock type, while XBlockStudioConfiguration
        # is a whitelist and uses a combination of xblock type and template (and in addition has a global feature flag),
        # it is expected that Studio code will need to filter by both disabled_xblocks and authorable_xblocks.
        authorable_xblock_names = [block.name for block in authorable_xblocks(allow_unsupported=True)]
        self.assertItemsEqual(
            ["survey", "done", "problem", "problem", "problem", "html", "split_module"],
            authorable_xblock_names
        )

    def test_authorable_blocks_by_name(self):
        """
        Tests authorable_xblocks when configuration flag is enabled and name is specified.
        """
        def verify_xblock_fields(name, template, support_level, block):
            """
            Verifies the returned xblock state.
            """
            self.assertEqual(name, block.name)
            self.assertEqual(template, block.template)
            self.assertEqual(support_level, block.support_level)

        XBlockStudioConfigurationFlag(enabled=True).save()

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
