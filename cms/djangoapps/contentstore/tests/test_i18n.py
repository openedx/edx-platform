"""
Tests for validate Internationalization and XBlock i18n service.
"""
import gettext
from unittest import mock, skip

from django.utils import translation
from edx_toggles.toggles.testutils import override_waffle_flag

from django.utils.translation import get_language
from xblock.core import XBlock
from xmodule.modulestore.django import XBlockI18nService
from xmodule.modulestore.tests.django_utils import TEST_DATA_SPLIT_MODULESTORE, ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, BlockFactory
from xmodule.tests.test_export import PureXBlock

from cms.djangoapps.contentstore import toggles
from cms.djangoapps.contentstore.tests.utils import AjaxEnabledTestClient
from cms.djangoapps.contentstore.views.preview import _prepare_runtime_for_preview
from common.djangoapps.student.tests.factories import UserFactory


class FakeTranslations(XBlockI18nService):
    """A test GNUTranslations class that takes a map of msg -> translations."""

    def __init__(self, translations):  # pylint: disable=super-init-not-called
        self.translations = translations

    def ugettext(self, msgid):
        """
        Mock override for ugettext translation operation
        """
        return self.translations.get(msgid, msgid)

    gettext = ugettext

    @staticmethod
    def translator(locales_map):  # pylint: disable=method-hidden
        """Build mock translator for the given locales.
        Returns a mock gettext.translation function that uses
        individual TestTranslations to translate in the given locales.
        :param locales_map: A map from locale name to a translations map.
                            {
                             'es': {'Hi': 'Hola', 'Bye': 'Adios'},
                             'zh': {'Hi': 'Ni Hao', 'Bye': 'Zaijian'}
                            }
        """
        def _translation(domain, localedir=None, languages=None):  # pylint: disable=unused-argument
            """
            return gettext.translation for given language
            """
            if languages:
                language = languages[0]
                if language in locales_map:
                    return FakeTranslations(locales_map[language])
            return gettext.NullTranslations()
        return _translation


class TestXBlockI18nService(ModuleStoreTestCase):
    """ Test XBlockI18nService """
    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE

    @XBlock.register_temp_plugin(PureXBlock, 'pure')
    def setUp(self):
        """ Setting up tests """
        super().setUp()
        self.test_language = 'dummy language'
        self.request = mock.Mock()
        self.course = CourseFactory.create()
        self.block = BlockFactory(category="pure", parent=self.course)
        _prepare_runtime_for_preview(self.request, self.block)
        self.addCleanup(translation.deactivate)

    def get_block_i18n_service(self, block):
        """
        return the block i18n service.
        """
        i18n_service = self.block.runtime.service(block, 'i18n')
        self.assertIsNotNone(i18n_service)
        self.assertIsInstance(i18n_service, XBlockI18nService)
        return i18n_service

    def test_django_service_translation_works(self):
        """
        Test django translation service works fine.
        """

        class wrap_ugettext_with_xyz:  # pylint: disable=invalid-name
            """
            A context manager function that just adds 'XYZ ' to the front
            of all strings of the module ugettext function.
            """

            def __init__(self, module):
                self.module = module
                self.old_ugettext = module.gettext

            def __enter__(self):
                def new_ugettext(*args, **kwargs):
                    """ custom function """
                    output = self.old_ugettext(*args, **kwargs)
                    return "XYZ " + output
                self.module.ugettext = new_ugettext
                self.module.gettext = new_ugettext

            def __exit__(self, _type, _value, _traceback):
                self.module.ugettext = self.old_ugettext
                self.module.gettext = self.old_ugettext

        i18n_service = self.get_block_i18n_service(self.block)

        # Activate french, so that if the fr files haven't been loaded, they will be loaded now.
        with translation.override("fr"):
            french_translation = translation.trans_real._active.value  # pylint: disable=protected-access

            # wrap the ugettext functions so that 'XYZ ' will prefix each translation
            with wrap_ugettext_with_xyz(french_translation):
                self.assertEqual(i18n_service.ugettext(self.test_language), 'XYZ dummy language')

            # Check that the old ugettext has been put back into place
            self.assertEqual(i18n_service.ugettext(self.test_language), 'dummy language')

    @mock.patch('django.utils.translation.gettext', mock.Mock(return_value='XYZ-TEST-LANGUAGE'))
    def test_django_translator_in_use_with_empty_block(self):
        """
        Test: Django default translator should in use if we have an empty block
        """
        i18n_service = XBlockI18nService(None)
        self.assertEqual(i18n_service.ugettext(self.test_language), 'XYZ-TEST-LANGUAGE')

    @mock.patch('django.utils.translation.gettext', mock.Mock(return_value='XYZ-TEST-LANGUAGE'))
    def test_message_catalog_translations(self):
        """
        Test: Message catalog from FakeTranslation should return required translations.
        """
        _translator = FakeTranslations.translator(
            {
                'es': {'Hello': 'es-hello-world'},
                'fr': {'Hello': 'fr-hello-world'},
            },
        )
        localedir = '/translations'
        translation.activate("es")
        with mock.patch('gettext.translation', return_value=_translator(domain='text', localedir=localedir,
                                                                        languages=[get_language()])):
            i18n_service = self.get_block_i18n_service(self.block)
            self.assertEqual(i18n_service.ugettext('Hello'), 'es-hello-world')

        translation.activate("ar")
        with mock.patch('gettext.translation', return_value=_translator(domain='text', localedir=localedir,
                                                                        languages=[get_language()])):
            i18n_service = self.get_block_i18n_service(self.block)
            self.assertEqual(i18n_service.gettext('Hello'), 'Hello')
            self.assertNotEqual(i18n_service.gettext('Hello'), 'fr-hello-world')
            self.assertNotEqual(i18n_service.gettext('Hello'), 'es-hello-world')

        translation.activate("fr")
        with mock.patch('gettext.translation', return_value=_translator(domain='text', localedir=localedir,
                                                                        languages=[get_language()])):
            i18n_service = self.get_block_i18n_service(self.block)
            self.assertEqual(i18n_service.ugettext('Hello'), 'fr-hello-world')

    def test_i18n_service_callable(self):
        """
        Test: i18n service should be callable in studio.
        """
        self.assertTrue(callable(self.block.runtime._services.get('i18n')))  # pylint: disable=protected-access


class InternationalizationTest(ModuleStoreTestCase):
    """
    Tests to validate Internationalization.
    """

    CREATE_USER = False

    def setUp(self):
        """
        These tests need a user in the DB so that the django Test Client
        can log them in.
        They inherit from the ModuleStoreTestCase class so that the mongodb collection
        will be cleared out before each test case execution and deleted
        afterwards.
        """
        super().setUp()

        self.uname = 'testuser'
        self.email = 'test+courses@edx.org'
        self.password = self.TEST_PASSWORD

        # Create the use so we can log them in.
        self.user = UserFactory.create(username=self.uname, email=self.email, password=self.password)

        # Note that we do not actually need to do anything
        # for registration if we directly mark them active.
        self.user.is_active = True
        # Staff has access to view all courses
        self.user.is_staff = True
        self.user.save()

        self.course_data = {
            'org': 'MITx',
            'number': '999',
            'display_name': 'Robot Super Course',
        }

    @override_waffle_flag(toggles.LEGACY_STUDIO_HOME, True)
    def test_course_plain_english(self):
        """Test viewing the index page with no courses"""
        self.client = AjaxEnabledTestClient()  # lint-amnesty, pylint: disable=attribute-defined-outside-init
        self.client.login(username=self.uname, password=self.password)

        resp = self.client.get_html('/home/')
        self.assertContains(resp,
                            '<h1 class="page-header">𝓢𝓽𝓾𝓭𝓲𝓸 Home</h1>',
                            status_code=200,
                            html=True)

    @override_waffle_flag(toggles.LEGACY_STUDIO_HOME, True)
    def test_course_explicit_english(self):
        """Test viewing the index page with no courses"""
        self.client = AjaxEnabledTestClient()  # lint-amnesty, pylint: disable=attribute-defined-outside-init
        self.client.login(username=self.uname, password=self.password)

        resp = self.client.get_html(
            '/home/',
            {},
            HTTP_ACCEPT_LANGUAGE='en',
        )

        self.assertContains(resp,
                            '<h1 class="page-header">𝓢𝓽𝓾𝓭𝓲𝓸 Home</h1>',
                            status_code=200,
                            html=True)

    # ****
    # NOTE:
    # ****
    #
    # This test will break when we replace this fake 'test' language
    # with actual Esperanto. This test will need to be updated with
    # actual Esperanto at that time.
    # Test temporarily disable since it depends on creation of dummy strings
    @skip
    def test_course_with_accents(self):
        """Test viewing the index page with no courses"""
        self.client = AjaxEnabledTestClient()  # lint-amnesty, pylint: disable=attribute-defined-outside-init
        self.client.login(username=self.uname, password=self.password)

        resp = self.client.get_html(
            '/home/',
            {},
            HTTP_ACCEPT_LANGUAGE='eo'
        )

        TEST_STRING = (
            '<h1 class="title-1">'
            'My \xc7\xf6\xfcrs\xe9s L#'
            '</h1>'
        )

        self.assertContains(resp,
                            TEST_STRING,
                            status_code=200,
                            html=True)
