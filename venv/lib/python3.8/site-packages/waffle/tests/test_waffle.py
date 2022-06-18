import logging
import random
import threading
import unittest

from django.contrib.auth import get_user_model
from django.conf import settings
from django.contrib.auth.models import AnonymousUser, Group
from django.db import connection, transaction
from django.test import RequestFactory, TransactionTestCase

from django.test.utils import override_settings

import mock

import waffle
from test_app import views
from test_app.models import CompanyAwareFlag, Company
from waffle.middleware import WaffleMiddleware
from waffle.models import Sample, Switch
from waffle.tests.base import TestCase


DATABASES = {'default', 'readonly'}


def get(**kw):
    request = RequestFactory().get('/foo', data=kw)
    request.user = AnonymousUser()
    return request


def process_request(request, view):
    response = view(request)
    return WaffleMiddleware().process_response(request, response)


class WaffleTests(TestCase):
    databases = DATABASES

    def assert_flag_dynamically_created_with_value(self, expected_value):
        FLAG_NAME = 'my_dynamically_created_flag'
        flag_model = waffle.get_waffle_flag_model()

        assert flag_model.objects.count() == 0
        assert expected_value == waffle.flag_is_active(get(), FLAG_NAME)
        assert flag_model.objects.count() == 1

        flag = flag_model.objects.get(name=FLAG_NAME)
        assert flag.name == FLAG_NAME

        # We assert no queries are made to ensure flags created when the
        # `CREATE_MISSING_FLAGS` setting is active are properly cached.
        with self.assertNumQueries(0):
            assert expected_value == waffle.flag_is_active(get(), FLAG_NAME)

    def test_persist_active_flag(self):
        waffle.get_waffle_flag_model().objects.create(name='myflag', percent='0.1')
        request = get()

        # Flag stays on.
        request.COOKIES['dwf_myflag'] = 'True'
        response = process_request(request, views.flag_in_view)
        self.assertEqual(b'on', response.content)
        assert 'dwf_myflag' in response.cookies
        self.assertEqual('True', response.cookies['dwf_myflag'].value)

    def test_persist_inactive_flag(self):
        waffle.get_waffle_flag_model().objects.create(name='myflag', percent='99.9')
        request = get()

        # Flag stays off.
        request.COOKIES['dwf_myflag'] = 'False'
        response = process_request(request, views.flag_in_view)
        self.assertEqual(b'off', response.content)
        assert 'dwf_myflag' in response.cookies
        self.assertEqual('False', response.cookies['dwf_myflag'].value)

    def test_no_set_unused_flag(self):
        """An unused flag shouldn't have its cookie reset."""
        request = get()
        request.COOKIES['dwf_unused'] = 'True'
        response = process_request(request, views.flag_in_view)
        assert 'dwf_unused' not in response.cookies

    def test_superuser(self):
        """Test the superuser switch."""
        waffle.get_waffle_flag_model().objects.create(name='myflag', superusers=True)
        request = get()
        response = process_request(request, views.flag_in_view)
        self.assertEqual(b'off', response.content)
        assert 'dwf_myflag' not in response.cookies

        superuser = get_user_model()(username='foo', is_superuser=True)
        request.user = superuser
        response = process_request(request, views.flag_in_view)
        self.assertEqual(b'on', response.content)
        assert 'dwf_myflag' not in response.cookies

        non_superuser = get_user_model()(username='bar', is_superuser=False)
        non_superuser.save()
        request.user = non_superuser
        response = process_request(request, views.flag_in_view)
        self.assertEqual(b'off', response.content)
        assert 'dwf_myflag' not in response.cookies

    def test_staff(self):
        """Test the staff switch."""
        waffle.get_waffle_flag_model().objects.create(name='myflag', staff=True)
        request = get()
        response = process_request(request, views.flag_in_view)
        self.assertEqual(b'off', response.content)
        assert 'dwf_myflag' not in response.cookies

        staff = get_user_model()(username='foo', is_staff=True)
        request.user = staff
        response = process_request(request, views.flag_in_view)
        self.assertEqual(b'on', response.content)
        assert 'dwf_myflag' not in response.cookies

        non_staff = get_user_model()(username='foo', is_staff=False)
        non_staff.save()
        request.user = non_staff
        response = process_request(request, views.flag_in_view)
        self.assertEqual(b'off', response.content)
        assert 'dwf_myflag' not in response.cookies

    def test_languages(self):
        waffle.get_waffle_flag_model().objects.create(name='myflag', languages='en,fr')
        request = get()
        response = process_request(request, views.flag_in_view)
        self.assertEqual(b'off', response.content)

        request.LANGUAGE_CODE = 'en'
        response = process_request(request, views.flag_in_view)
        self.assertEqual(b'on', response.content)

        request.LANGUAGE_CODE = 'de'
        response = process_request(request, views.flag_in_view)
        self.assertEqual(b'off', response.content)

    def test_user(self):
        """Test the per-user switch."""
        user = get_user_model().objects.create(username='foo')
        flag = waffle.get_waffle_flag_model().objects.create(name='myflag')
        flag.users.add(user)

        request = get()
        request.user = user
        response = process_request(request, views.flag_in_view)
        self.assertEqual(b'on', response.content)
        assert 'dwf_myflag' not in response.cookies

        request.user = get_user_model().objects.create(username='someone_else')
        response = process_request(request, views.flag_in_view)
        self.assertEqual(b'off', response.content)
        assert 'dwf_myflag' not in response.cookies

        # Unsetting the flag on a user should have an effect.
        flag.users.remove(user)
        request.user = user
        response = process_request(request, views.flag_in_view)
        self.assertEqual(b'off', response.content)

    def test_remove_from_user(self):
        """Same operation of `test_user` but performed with reverse relation"""
        user = get_user_model().objects.create(username='foo')
        flag = waffle.get_waffle_flag_model().objects.create(name='myflag')
        flag.users.add(user)

        request = get()
        request.user = user
        response = process_request(request, views.flag_in_view)
        self.assertEqual(b'on', response.content)
        assert 'dwf_myflag' not in response.cookies

        request.user = get_user_model().objects.create(username='someone_else')
        response = process_request(request, views.flag_in_view)
        self.assertEqual(b'off', response.content)
        assert 'dwf_myflag' not in response.cookies

        # Unsetting the flag on a user should have an effect.
        user.flag_set.remove(flag)
        request.user = user
        response = process_request(request, views.flag_in_view)
        self.assertEqual(b'off', response.content)

    def test_group(self):
        """Test the per-group switch."""
        group = Group.objects.create(name='foo')
        user = get_user_model().objects.create(username='bar')
        user.groups.add(group)

        flag = waffle.get_waffle_flag_model().objects.create(name='myflag')
        flag.groups.add(group)

        request = get()
        request.user = user
        response = process_request(request, views.flag_in_view)
        self.assertEqual(b'on', response.content)
        assert 'dwf_myflag' not in response.cookies

        request.user = get_user_model()(username='someone_else')
        request.user.save()
        response = process_request(request, views.flag_in_view)
        self.assertEqual(b'off', response.content)
        assert 'dwf_myflag' not in response.cookies

        # Unsetting the flag on a group should have an effect.
        flag.groups.remove(group)
        request.user = user
        response = process_request(request, views.flag_in_view)
        self.assertEqual(b'off', response.content)

    def test_remove_from_group(self):
        """Same operation of `test_group` but performed with reverse relation"""
        group = Group.objects.create(name='foo')
        user = get_user_model().objects.create(username='bar')
        user.groups.add(group)

        flag = waffle.get_waffle_flag_model().objects.create(name='myflag')
        flag.groups.add(group)

        request = get()
        request.user = user
        response = process_request(request, views.flag_in_view)
        self.assertEqual(b'on', response.content)
        assert 'dwf_myflag' not in response.cookies

        request.user = get_user_model()(username='someone_else')
        request.user.save()
        response = process_request(request, views.flag_in_view)
        self.assertEqual(b'off', response.content)
        assert 'dwf_myflag' not in response.cookies

        # Unsetting the flag on a group should have an effect.
        group.flag_set.remove(flag)
        request.user = user
        response = process_request(request, views.flag_in_view)
        self.assertEqual(b'off', response.content)

    def test_authenticated(self):
        """Test the authenticated/anonymous switch."""
        waffle.get_waffle_flag_model().objects.create(name='myflag', authenticated=True)

        request = get()
        response = process_request(request, views.flag_in_view)
        self.assertEqual(b'off', response.content)
        assert 'dwf_myflag' not in response.cookies

        request.user = get_user_model()(username='foo')
        assert request.user.is_authenticated
        response = process_request(request, views.flag_in_view)
        self.assertEqual(b'on', response.content)
        assert 'dwf_myflag' not in response.cookies

    def test_everyone_on(self):
        """Test the 'everyone' switch on."""
        waffle.get_waffle_flag_model().objects.create(name='myflag', everyone=True)

        request = get()
        request.COOKIES['dwf_myflag'] = 'False'
        response = process_request(request, views.flag_in_view)
        self.assertEqual(b'on', response.content)
        assert 'dwf_myflag' not in response.cookies

        request.user = get_user_model()(username='foo')
        assert request.user.is_authenticated
        response = process_request(request, views.flag_in_view)
        self.assertEqual(b'on', response.content)
        assert 'dwf_myflag' not in response.cookies

    def test_everyone_off(self):
        """Test the 'everyone' switch off."""
        waffle.get_waffle_flag_model().objects.create(name='myflag', everyone=False, authenticated=True)

        request = get()
        request.COOKIES['dwf_myflag'] = 'True'
        response = process_request(request, views.flag_in_view)
        self.assertEqual(b'off', response.content)
        assert 'dwf_myflag' not in response.cookies

        request.user = get_user_model()(username='foo')
        assert request.user.is_authenticated
        response = process_request(request, views.flag_in_view)
        self.assertEqual(b'off', response.content)
        assert 'dwf_myflag' not in response.cookies

    def test_percent(self):
        """If you have no cookie, you get a cookie!"""
        waffle.get_waffle_flag_model().objects.create(name='myflag', percent='50.0')
        request = get()
        response = process_request(request, views.flag_in_view)
        assert 'dwf_myflag' in response.cookies

    @mock.patch.object(random, 'uniform')
    def test_reroll(self, uniform):
        """Even without a cookie, calling flag_is_active twice should return
        the same value."""
        waffle.get_waffle_flag_model().objects.create(name='myflag', percent='50.0')
        # Make sure we're not really random.
        request = get()  # Create a clean request.
        assert not hasattr(request, 'waffles')
        uniform.return_value = '10'  # < 50. Flag is True.
        assert waffle.flag_is_active(request, 'myflag')
        assert hasattr(request, 'waffles')  # We should record this flag.
        assert 'myflag' in request.waffles
        assert request.waffles['myflag'][0]
        uniform.return_value = '70'  # > 50. Normally, Flag would be False.
        assert waffle.flag_is_active(request, 'myflag')
        assert request.waffles['myflag'][0]

    def test_undefined(self):
        """Undefined flags are always false."""
        request = get()
        assert not waffle.flag_is_active(request, 'foo')

    @override_settings(WAFFLE_FLAG_DEFAULT=True)
    def test_undefined_default(self):
        """WAFFLE_FLAG_DEFAULT controls undefined flags."""
        request = get()
        assert waffle.flag_is_active(request, 'foo')

    @override_settings(WAFFLE_OVERRIDE=True)
    def test_override(self):
        request = get(foo='1')
        waffle.get_waffle_flag_model().objects.create(name='foo')  # Off for everyone.
        assert waffle.flag_is_active(request, 'foo')

    def test_testing_flag(self):
        waffle.get_waffle_flag_model().objects.create(name='foo', testing=True)
        request = get(dwft_foo='1')
        assert waffle.flag_is_active(request, 'foo')
        assert 'foo' in request.waffle_tests
        assert request.waffle_tests['foo']

        # GET param should override cookie
        request = get(dwft_foo='0')
        request.COOKIES['dwft_foo'] = 'True'
        assert not waffle.flag_is_active(request, 'foo')
        assert 'foo' in request.waffle_tests
        assert not request.waffle_tests['foo']

    def test_testing_disabled_flag(self):
        waffle.get_waffle_flag_model().objects.create(name='foo')
        request = get(dwft_foo='1')
        assert not waffle.flag_is_active(request, 'foo')
        assert not hasattr(request, 'waffle_tests')

        request = get(dwft_foo='0')
        assert not waffle.flag_is_active(request, 'foo')
        assert not hasattr(request, 'waffle_tests')

    def test_testing_flag_header(self):
        waffle.get_waffle_flag_model().objects.create(name='foo', testing=True)
        request = RequestFactory().get('/foo', HTTP_DWFT_FOO='1')
        request.user = AnonymousUser()
        assert waffle.flag_is_active(request, 'foo')
        assert 'foo' in request.waffle_tests
        assert request.waffle_tests['foo']

        # header should override cookie
        request = RequestFactory().get('/foo', HTTP_DWFT_FOO='0')
        request.user = AnonymousUser()
        request.COOKIES['dwft_foo'] = 'True'
        assert not waffle.flag_is_active(request, 'foo')
        assert 'foo' in request.waffle_tests
        assert not request.waffle_tests['foo']

    def test_set_then_unset_testing_flag(self):
        waffle.get_waffle_flag_model().objects.create(name='myflag', testing=True)
        response = self.client.get('/flag_in_view?dwft_myflag=1')
        self.assertEqual(b'on', response.content)

        response = self.client.get('/flag_in_view')
        self.assertEqual(b'on', response.content)

        response = self.client.get('/flag_in_view?dwft_myflag=0')
        self.assertEqual(b'off', response.content)

        response = self.client.get('/flag_in_view')
        self.assertEqual(b'off', response.content)

        response = self.client.get('/flag_in_view?dwft_myflag=1')
        self.assertEqual(b'on', response.content)

    @override_settings(DATABASE_ROUTERS=['waffle.tests.base.ReplicationRouter'])
    def test_everyone_on_read_from_write_db(self):
        flag = waffle.get_waffle_flag_model().objects.create(name='myflag', everyone=True)

        request = get()
        response = process_request(request, views.flag_in_view)
        # By default, flag_is_active should hit whatever it configured as the
        # read DB (so values will be stale if replication is lagged).
        self.assertEqual(b'off', response.content)

        with override_settings(WAFFLE_READ_FROM_WRITE_DB=True):
            # Save the flag again to flush the cache.
            flag.save()

            # The next read should now be directed to the write DB, ensuring
            # the cache and DB are in sync.
            response = process_request(request, views.flag_in_view)
            self.assertEqual(b'on', response.content)

    @override_settings(WAFFLE_FLAG_MODEL='test_app.CompanyAwareFlag', AUTH_USER_MODEL='test_app.CompanyUser')
    def test_pluggable_model(self):
        flag_model = waffle.get_waffle_flag_model()
        self.assertEqual(CompanyAwareFlag, flag_model)

        acme_company = Company.objects.create(name='Acme Ltd.')
        feline_company = Company.objects.create(name='Feline LLC')

        acme_company_flag = waffle.get_waffle_flag_model().objects.create(name='myflag', superusers=True)
        acme_company_flag.companies.add(acme_company)

        request = get()
        response = process_request(request, views.flag_in_view)
        self.assertEqual(b'off', response.content)
        assert 'dwf_myflag' not in response.cookies

        acme_user = get_user_model()(username='acme.mcfield', company=acme_company)
        request.user = acme_user
        response = process_request(request, views.flag_in_view)
        self.assertEqual(b'on', response.content)
        assert 'dwf_myflag' not in response.cookies

        feline_user = get_user_model()(username='acme.mcfield', company=feline_company)
        request.user = feline_user
        response = process_request(request, views.flag_in_view)
        self.assertEqual(b'off', response.content)
        assert 'dwf_myflag' not in response.cookies

    @override_settings(WAFFLE_CREATE_MISSING_FLAGS=True)
    @override_settings(WAFFLE_FLAG_DEFAULT=False)
    def test_flag_created_dynamically_default_false(self):
        self.assert_flag_dynamically_created_with_value(False)

    @override_settings(WAFFLE_CREATE_MISSING_FLAGS=True)
    @override_settings(WAFFLE_FLAG_DEFAULT=True)
    def test_flag_created_dynamically_default_true(self):
        self.assert_flag_dynamically_created_with_value(True)

    @mock.patch('waffle.models.logger')
    def test_no_logging_missing_flag_by_default(self, mock_logger):
        request = get()
        waffle.flag_is_active(request, 'foo')
        mock_logger.log.call_count == 0

    @override_settings(WAFFLE_LOG_MISSING_FLAGS=logging.WARNING)
    @mock.patch('waffle.models.logger')
    def test_logging_missing_flag(self, mock_logger):
        request = get()
        waffle.flag_is_active(request, 'foo')
        mock_logger.log.assert_called_with(logging.WARNING, 'Flag %s not found', 'foo')


class SwitchTests(TestCase):
    databases = DATABASES

    def assert_switch_dynamically_created_with_value(self, expected_value):
        SWITCH_NAME = 'my_dynamically_created_switch'

        assert Switch.objects.count() == 0
        assert expected_value == waffle.switch_is_active(SWITCH_NAME)
        assert Switch.objects.count() == 1

        switch = Switch.objects.get(name=SWITCH_NAME)
        assert switch.name == SWITCH_NAME
        assert expected_value == switch.active

        # We assert no queries are made to ensure switches created when the
        # `CREATE_MISSING_SWITCHES` setting is active are properly cached.
        with self.assertNumQueries(0):
            assert expected_value == waffle.switch_is_active(SWITCH_NAME)

    def test_switch_active(self):
        switch = Switch.objects.create(name='myswitch', active=True)
        assert waffle.switch_is_active(switch.name)

    def test_switch_inactive(self):
        switch = Switch.objects.create(name='myswitch', active=False)
        assert not waffle.switch_is_active(switch.name)

    def test_switch_active_from_cache(self):
        """Do not make two queries for an existing active switch."""
        switch = Switch.objects.create(name='myswitch', active=True)
        # Get the value once so that it will be put into the cache
        assert waffle.switch_is_active(switch.name)
        queries = len(connection.queries)
        assert waffle.switch_is_active(switch.name)
        self.assertEqual(queries, len(connection.queries))

    def test_switch_inactive_from_cache(self):
        """Do not make two queries for an existing inactive switch."""
        switch = Switch.objects.create(name='myswitch', active=False)
        # Get the value once so that it will be put into the cache
        assert not waffle.switch_is_active(switch.name)
        queries = len(connection.queries)
        assert not waffle.switch_is_active(switch.name)
        self.assertEqual(queries, len(connection.queries))

    def test_undefined(self):
        assert not waffle.switch_is_active('foo')

    @override_settings(WAFFLE_SWITCH_DEFAULT=True)
    def test_undefined_default(self):
        assert waffle.switch_is_active('foo')

    @override_settings(DEBUG=True)
    def test_no_query(self):
        """Do not make two queries for a non-existent switch."""
        assert not Switch.objects.filter(name='foo').exists()
        queries = len(connection.queries)
        assert not waffle.switch_is_active('foo')
        assert len(connection.queries) > queries
        queries = len(connection.queries)
        assert not waffle.switch_is_active('foo')
        self.assertEqual(queries, len(connection.queries))

    @override_settings(DATABASE_ROUTERS=['waffle.tests.base.ReplicationRouter'])
    def test_read_from_write_db(self):
        switch = Switch.objects.create(name='switch', active=True)

        # By default, switch_is_active should hit whatever it configured as the
        # read DB (so values will be stale if replication is lagged).
        assert not waffle.switch_is_active(switch.name)

        with override_settings(WAFFLE_READ_FROM_WRITE_DB=True):
            # Save the switch again to flush the cache.
            switch.save()

            # The next read should now be directed to the write DB, ensuring
            # the cache and DB are in sync.
            assert waffle.switch_is_active(switch.name)

    @override_settings(WAFFLE_CREATE_MISSING_SWITCHES=True)
    @override_settings(WAFFLE_SWITCH_DEFAULT=False)
    def test_switch_created_dynamically_false(self):
        self.assert_switch_dynamically_created_with_value(False)

    @override_settings(WAFFLE_CREATE_MISSING_SWITCHES=True)
    @override_settings(WAFFLE_SWITCH_DEFAULT=True)
    def test_switch_created_dynamically_true(self):
        self.assert_switch_dynamically_created_with_value(True)

    @mock.patch('waffle.models.logger')
    def test_no_logging_missing_switch_by_default(self, mock_logger):
        waffle.switch_is_active('foo')
        mock_logger.log.call_count == 0

    @override_settings(WAFFLE_LOG_MISSING_SWITCHES=logging.WARNING)
    @mock.patch('waffle.models.logger')
    def test_logging_missing_switch(self, mock_logger):
        waffle.switch_is_active('foo')
        mock_logger.log.assert_called_with(logging.WARNING, 'Switch %s not found', 'foo')


class SampleTests(TestCase):
    databases = DATABASES

    def assert_sample_dynamically_created_with_value(self, is_active, expected_value):
        SAMPLE_NAME = 'my_dynamically_created_sample'

        assert Sample.objects.count() == 0
        assert is_active == waffle.sample_is_active(SAMPLE_NAME)
        assert Sample.objects.count() == 1

        sample = Sample.objects.get(name=SAMPLE_NAME)

        assert sample.name == SAMPLE_NAME
        assert sample.percent == expected_value

        # We assert no queries are made to ensure samples created when the
        # `CREATE_MISSING_SAMPLES` setting is active are properly cached.
        with self.assertNumQueries(0):
            assert is_active == waffle.sample_is_active(SAMPLE_NAME)

    def test_sample_100(self):
        sample = Sample.objects.create(name='sample', percent='100.0')
        assert waffle.sample_is_active(sample.name)

    def test_sample_0(self):
        sample = Sample.objects.create(name='sample', percent='0.0')
        assert not waffle.sample_is_active(sample.name)

    def test_undefined(self):
        assert not waffle.sample_is_active('foo')

    @override_settings(WAFFLE_SAMPLE_DEFAULT=True)
    def test_undefined_default(self):
        assert waffle.sample_is_active('foo')

    @override_settings(DATABASE_ROUTERS=['waffle.tests.base.ReplicationRouter'])
    def test_read_from_write_db(self):
        sample = Sample.objects.create(name='sample', percent='100.0')

        # By default, sample_is_active should hit whatever it configured as the
        # read DB (so values will be stale if replication is lagged).
        assert not waffle.sample_is_active(sample.name)

        with override_settings(WAFFLE_READ_FROM_WRITE_DB=True):
            # Save the sample again to flush the cache.
            sample.save()

            # The next read should now be directed to the write DB, ensuring
            # the cache and DB are in sync.
            assert waffle.sample_is_active(sample.name)

    @override_settings(WAFFLE_CREATE_MISSING_SAMPLES=True)
    @override_settings(WAFFLE_SAMPLE_DEFAULT=False)
    def test_sample_created_dynamically_default_false(self):
        self.assert_sample_dynamically_created_with_value(False, 0.0)

    @override_settings(WAFFLE_CREATE_MISSING_SAMPLES=True)
    @override_settings(WAFFLE_SAMPLE_DEFAULT=True)
    def test_sample_created_dynamically_default_true(self):
        self.assert_sample_dynamically_created_with_value(True, 100.0)

    @mock.patch('waffle.models.logger')
    def test_no_logging_missing_sample_by_default(self, mock_logger):
        waffle.switch_is_active('foo')
        mock_logger.log.call_count == 0

    @override_settings(WAFFLE_LOG_MISSING_SAMPLES=logging.WARNING)
    @mock.patch('waffle.models.logger')
    def test_logging_missing_sample(self, mock_logger):
        waffle.sample_is_active('foo')
        mock_logger.log.assert_called_with(logging.WARNING, 'Sample %s not found', 'foo')


class TransactionTestMixin(object):
    """Mixin providing an abstract test case for writing in a transaction.
    """
    def create_toggle(self):
        """Create an inactive feature toggle (i.e. flag, switch, sample)."""
        raise NotImplementedError

    def flip_toggle(self, toggle):
        """Flip the toggle to an active state."""
        raise NotImplementedError

    def toggle_is_active(self, toggle):
        """Use the built-in *_is_active helper to check the toggle's state."""
        raise NotImplementedError

    @unittest.skipIf('sqlite3' in settings.DATABASES['default']['ENGINE'],
                     'This test uses threads, which the sqlite3 DB engine '
                     'does not support.')
    def test_flip_toggle_in_transaction(self):
        """Wait to invalidate the cache until after the current transaction.

        This test covers a potential race condition where, if the cache were
        flushed in the middle of a transaction, the next read from the database
        (before the transaction is committed) would get a stale value and cache
        it. See #296 for more context.
        """
        toggle = self.create_toggle()
        self.addCleanup(toggle.delete)

        written_in_background_thread = threading.Event()
        read_in_main_thread = threading.Event()

        @transaction.atomic
        def update_toggle():
            self.flip_toggle(toggle)

            # Signal to the main thread that the toggle has been updated, but
            # the transaction is not yet committed.
            written_in_background_thread.set()

            # Pause here to allow the main thread to make an assertion.
            read_in_main_thread.wait(timeout=1)

        # Start a background thread to update the toggle in a transaction.
        t = threading.Thread(target=update_toggle)
        t.daemon = True
        t.start()

        # After the toggle is updated but before the transaction is committed,
        # the cache will still have the previous value.
        written_in_background_thread.wait(timeout=1)
        assert not self.toggle_is_active(toggle)

        # After the transaction is committed, the cache should have been
        # invalidated, hence the next call to *_is_active should have the
        # correct value.
        read_in_main_thread.set()
        t.join(timeout=1)
        assert self.toggle_is_active(toggle)


class FlagTransactionTests(TransactionTestMixin, TransactionTestCase):
    def create_toggle(self):
        return waffle.get_waffle_flag_model().objects.create(
            name='transaction-flag-name', everyone=False
        )

    def flip_toggle(self, flag):
        flag.everyone = True
        flag.save()

    def toggle_is_active(self, flag):
        return waffle.flag_is_active(get(), flag.name)


class SwitchTransactionTests(TransactionTestMixin, TransactionTestCase):
    def create_toggle(self):
        return Switch.objects.create(name='transaction-switch-name',
                                     active=False)

    def flip_toggle(self, switch):
        switch.active = True
        switch.save()

    def toggle_is_active(self, switch):
        return waffle.switch_is_active(switch.name)


class SampleTransactionTests(TransactionTestMixin, TransactionTestCase):
    def create_toggle(self):
        return Sample.objects.create(name='transaction-sample-name', percent=0)

    def flip_toggle(self, sample):
        sample.percent = 100
        sample.save()

    def toggle_is_active(self, sample):
        return waffle.sample_is_active(sample.name)
