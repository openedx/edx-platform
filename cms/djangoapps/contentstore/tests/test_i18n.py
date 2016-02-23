from unittest import skip

from django.contrib.auth.models import User

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from contentstore.tests.utils import AjaxEnabledTestClient
from xmodule.modulestore.django import ModuleI18nService
from django.utils import translation
from django.utils.translation import get_language
from django.conf import settings
import mock
import gettext


class FakeTranslations(ModuleI18nService):
    """A test GNUTranslations class that takes a map of msg -> translations."""

    def __init__(self, translations):  # pylint: disable=super-init-not-called
        self.translations = translations

    def ugettext(self, msgid):
        return self.translations.get(msgid, msgid)

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


class TestModuleI18nService(ModuleStoreTestCase):
    """ Test ModuleI18nService """

    xblock_name = 'dummy_block'

    def setUp(self):
        """ Setting up tests """
        super(TestModuleI18nService, self).setUp()
        self.test_language = 'dummy language'
        self.xblock_mock = mock.Mock()
        self.xblock_mock.unmixed_class.__name__ = self.xblock_name
        self.i18n_service = ModuleI18nService(self.xblock_mock)
        self.addCleanup(translation.activate, settings.LANGUAGE_CODE)

    def test_django_service_translation_works(self):
        """
        Test django translation service works fine.
        """

        def wrap_with_xyz(func):
            """
            A decorator function that just adds 'XYZ ' to the front of all strings
            """
            def new_func(*args, **kwargs):
                """ custom function """
                output = func(*args, **kwargs)
                return "XYZ " + output
            return new_func

        old_lang = translation.get_language()

        # Activate french, so that if the fr files haven't been loaded, they will be loaded now.
        translation.activate("fr")
        french_translation = translation.trans_real._active.value  # pylint: disable=protected-access

        # wrap the ugettext functions so that 'TEST ' will prefix each translation
        french_translation.ugettext = wrap_with_xyz(french_translation.ugettext)
        self.assertEqual(self.i18n_service.ugettext(self.test_language), 'XYZ dummy language')

        # Turn back on our old translations
        translation.activate(old_lang)
        del old_lang
        self.assertEqual(self.i18n_service.ugettext(self.test_language), 'dummy language')

    @mock.patch('django.utils.translation.ugettext', mock.Mock(return_value='XYZ-TEST-LANGUAGE'))
    def test_django_translator_in_use_with_empty_block(self):
        """
        Test: Django default translator should in use if we have an empty block
        """
        self.assertEqual(ModuleI18nService(block=None).ugettext(self.test_language), 'XYZ-TEST-LANGUAGE')

    @mock.patch('django.utils.translation.ugettext', mock.Mock(return_value='XYZ-TEST-LANGUAGE'))
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
        localedir = '/conf/locale'
        translation.activate("es")
        with mock.patch('gettext.translation', return_value=_translator(domain='domain', localedir=localedir,
                                                                        languages=[get_language()])):
            self.assertEqual(ModuleI18nService(self.xblock_mock).ugettext('Hello'), 'es-hello-world')

        translation.activate("ar")
        with mock.patch('gettext.translation', return_value=_translator(domain='domain', localedir=localedir,
                                                                        languages=[get_language()])):
            i18n_service_2 = ModuleI18nService(self.xblock_mock)
            self.assertEqual(i18n_service_2.ugettext('Hello'), 'Hello')
            self.assertNotEqual(i18n_service_2.ugettext('Hello'), 'fr-hello-world')
            self.assertNotEqual(i18n_service_2.ugettext('Hello'), 'es-hello-world')

        translation.activate("fr")
        with mock.patch('gettext.translation', return_value=_translator(domain='domain', localedir=localedir,
                                                                        languages=[get_language()])):
            self.assertEqual(ModuleI18nService(self.xblock_mock).ugettext('Hello'), 'fr-hello-world')

        # Django default translator should in use if we block is missing.
        with mock.patch('gettext.translation', return_value=_translator(domain='domain', localedir=localedir,
                                                                        languages=[get_language()])):
            self.assertEqual(ModuleI18nService(block=None).ugettext('Hello'), 'XYZ-TEST-LANGUAGE')


class InternationalizationTest(ModuleStoreTestCase):
    """
    Tests to validate Internationalization.
    """

    def setUp(self):
        """
        These tests need a user in the DB so that the django Test Client
        can log them in.
        They inherit from the ModuleStoreTestCase class so that the mongodb collection
        will be cleared out before each test case execution and deleted
        afterwards.
        """
        super(InternationalizationTest, self).setUp(create_user=False)

        self.uname = 'testuser'
        self.email = 'test+courses@edx.org'
        self.password = 'foo'

        # Create the use so we can log them in.
        self.user = User.objects.create_user(self.uname, self.email, self.password)

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

    def test_course_plain_english(self):
        """Test viewing the index page with no courses"""
        self.client = AjaxEnabledTestClient()
        self.client.login(username=self.uname, password=self.password)

        resp = self.client.get_html('/home/')
        self.assertContains(resp,
                            '<h1 class="page-header">Studio Home</h1>',
                            status_code=200,
                            html=True)

    def test_course_explicit_english(self):
        """Test viewing the index page with no courses"""
        self.client = AjaxEnabledTestClient()
        self.client.login(username=self.uname, password=self.password)

        resp = self.client.get_html(
            '/home/',
            {},
            HTTP_ACCEPT_LANGUAGE='en',
        )

        self.assertContains(resp,
                            '<h1 class="page-header">Studio Home</h1>',
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
        self.client = AjaxEnabledTestClient()
        self.client.login(username=self.uname, password=self.password)

        resp = self.client.get_html(
            '/home/',
            {},
            HTTP_ACCEPT_LANGUAGE='eo'
        )

        TEST_STRING = (
            u'<h1 class="title-1">'
            u'My \xc7\xf6\xfcrs\xe9s L#'
            u'</h1>'
        )

        self.assertContains(resp,
                            TEST_STRING,
                            status_code=200,
                            html=True)
