"""
Tests for the Jabber Django app. The vast majority of the
functionality is in the utils module.
"""
from django.test import TestCase
from django.test.utils import override_settings
from django.core.exceptions import ImproperlyConfigured

from factory import DjangoModelFactory, Sequence

from jabber.models import JabberUser
import jabber.utils


class JabberUserFactory(DjangoModelFactory):
    """
    Simple factory for the JabberUser model.
    """
    FACTORY_FOR = JabberUser

    # username is a primary key, so each must be unique
    username = Sequence(lambda n: "johndoe_{0}".format(n))
    password = "abcdefg"


class UtilsTests(TestCase):
    """
    Tests for the various utility functions in the utils module.
    TODO: is there a better way to override all of these settings?
          It'd be nice to have a single dict that we just copy and
          override keys, but that almost looks uglier than this.
    """
    @override_settings(JABBER={
        'HOST': 'jabber.edx.org',
        'PORT': '5208',
        'PATH': 'http-bind/',
        'USE_SSL': False,
    })
    def test_get_bosh_url_standard(self):
        bosh_url = jabber.utils.get_bosh_url()
        self.assertEquals(bosh_url, 'http://jabber.edx.org:5208/http-bind/')

    @override_settings(JABBER={'HOST': 'jabber.edx.org'})
    def test_get_bosh_url_host_only(self):
        bosh_url = jabber.utils.get_bosh_url()
        self.assertEquals(bosh_url, 'http://jabber.edx.org')

    @override_settings(JABBER={
        'PORT': '5208',
        'PATH': 'http-bind/',
        'USE_SSL': False,
    })
    def test_get_bosh_url_no_host(self):
        with self.assertRaises(ImproperlyConfigured):
            jabber.utils.get_bosh_url()

    @override_settings(JABBER={
        'HOST': 'jabber.edx.org',
        'PORT': 5208,
        'PATH': 'http-bind/',
        'USE_SSL': False,
    })
    def test_get_bosh_url_numeric_port(self):
        bosh_url = jabber.utils.get_bosh_url()
        self.assertEquals(bosh_url, 'http://jabber.edx.org:5208/http-bind/')

    @override_settings(JABBER={
        'HOST': 'jabber.edx.org',
        'PORT': '5208',
        'PATH': 'http-bind/',
        'USE_SSL': True,
    })
    def test_get_bosh_url_use_ssl(self):
        bosh_url = jabber.utils.get_bosh_url()
        self.assertEquals(bosh_url, 'https://jabber.edx.org:5208/http-bind/')

    @override_settings(JABBER={
        'HOST': 'jabber.edx.org',
        'MUC_SUBDOMAIN': 'conference',
    })
    def test_get_room_name_for_course_standard(self):
        course_id = "MITx/6.002x/2013_Spring"
        room_name = jabber.utils.get_room_name_for_course(course_id)
        self.assertEquals(room_name, '2013_Spring_class@conference.jabber.edx.org')

    @override_settings(JABBER={'MUC_SUBDOMAIN': 'conference'})
    def test_get_room_name_for_course_no_host(self):
        course_id = "MITx/6.002x/2013_Spring"
        with self.assertRaises(ImproperlyConfigured):
            jabber.utils.get_room_name_for_course(course_id)

    @override_settings(JABBER={'HOST': 'jabber.edx.org'})
    def test_get_room_name_for_course_no_muc_subdomain(self):
        course_id = "MITx/6.002x/2013_Spring"
        room_name = jabber.utils.get_room_name_for_course(course_id)
        self.assertEquals(room_name, '2013_Spring_class@jabber.edx.org')

    @override_settings(JABBER={
        'HOST': 'jabber.edx.org',
        'MUC_SUBDOMAIN': 'conference',
    })
    def test_get_room_name_for_course_malformed_course_id(self):
        course_id = "MITx_6.002x_2013_Spring"
        with self.assertRaises(ValueError):
            jabber.utils.get_room_name_for_course(course_id)

        course_id = "MITx/6.002x_2013_Spring"
        with self.assertRaises(ValueError):
            jabber.utils.get_room_name_for_course(course_id)

        course_id = "MITx/6.002x/2013/Spring"
        with self.assertRaises(ValueError):
            jabber.utils.get_room_name_for_course(course_id)

    def test_get_password_for_existing_user(self):
        jabber_user = JabberUserFactory.create()
        pre_jabber_user_count = JabberUser.objects.count()
        password = jabber.utils.get_or_create_password_for_user(jabber_user.username)
        post_jabber_user_count = JabberUser.objects.count()
        jabber_user_delta = post_jabber_user_count - pre_jabber_user_count
        self.assertEquals(password, jabber_user.password)
        self.assertEquals(jabber_user_delta, 0)

    def test_get_password_for_nonexistent_user(self):
        pre_jabber_user_count = JabberUser.objects.count()
        jabber.utils.get_or_create_password_for_user("nonexistentuser")
        post_jabber_user_count = JabberUser.objects.count()
        jabber_user_delta = post_jabber_user_count - pre_jabber_user_count
        self.assertEquals(jabber_user_delta, 1)

