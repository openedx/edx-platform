"""Test safe_exec.py"""


import copy
import hashlib
import os
import os.path
import textwrap
import unittest
from unittest.mock import call, patch

import pytest
import random2 as random
from codejail import jail_code
from codejail.django_integration import ConfigureCodeJailMiddleware
from codejail.safe_exec import SafeExecException
from django.conf import settings
from django.core.exceptions import MiddlewareNotUsed
from django.test import override_settings
from six import unichr
from six.moves import range

from openedx.core.djangolib.testing.utils import skip_unless_lms
from xmodule.capa.safe_exec import safe_exec, update_hash
from xmodule.capa.safe_exec.remote_exec import is_codejail_in_darklaunch, is_codejail_rest_service_enabled
from xmodule.capa.safe_exec.safe_exec import emsg_normalizers, normalize_error_message
from xmodule.capa.tests.test_util import use_unsafe_codejail


@use_unsafe_codejail()
class TestSafeExec(unittest.TestCase):  # lint-amnesty, pylint: disable=missing-class-docstring
    def test_set_values(self):
        g = {}
        safe_exec("a = 17", g)
        assert g['a'] == 17

    def test_division(self):
        g = {}
        # Future division: 1/2 is 0.5.
        safe_exec("a = 1/2", g)
        assert g['a'] == 0.5

    def test_assumed_imports(self):
        g = {}
        # Math is always available.
        safe_exec("a = int(math.pi)", g)
        assert g['a'] == 3

    def test_random_seeding(self):
        g = {}
        r = random.Random(17)
        rnums = [r.randint(0, 999) for _ in range(100)]

        # Without a seed, the results are unpredictable
        safe_exec("rnums = [random.randint(0, 999) for _ in xrange(100)]", g)
        assert g['rnums'] != rnums

        # With a seed, the results are predictable
        safe_exec("rnums = [random.randint(0, 999) for _ in xrange(100)]", g, random_seed=17)
        assert g['rnums'] == rnums

    def test_random_is_still_importable(self):
        g = {}
        r = random.Random(17)
        rnums = [r.randint(0, 999) for _ in range(100)]

        # With a seed, the results are predictable even from the random module
        safe_exec(
            "import random\n"
            "rnums = [random.randint(0, 999) for _ in xrange(100)]\n",
            g, random_seed=17)
        assert g['rnums'] == rnums

    def test_python_lib(self):
        pylib = os.path.dirname(__file__) + "/test_files/pylib"
        g = {}
        safe_exec(
            "import constant; a = constant.THE_CONST",
            g, python_path=[pylib]
        )

    def test_raising_exceptions(self):
        g = {}
        with pytest.raises(SafeExecException) as cm:
            safe_exec("1/0", g)
        assert 'ZeroDivisionError' in str(cm.value)


class TestSafeOrNot(unittest.TestCase):  # lint-amnesty, pylint: disable=missing-class-docstring

    @skip_unless_lms
    def test_cant_do_something_forbidden(self):
        '''
        Demonstrates that running unsafe code inside the code jail
        throws SafeExecException, protecting the calling process.

        This test generally is skipped in CI due to its complex setup. That said, we recommend that devs who are
        hacking on CodeJail or advanced CAPA in any significant way take the time to make sure it passes locally.
        See either:
        * in-platform setup: https://github.com/openedx/edx-platform/blob/master/xmodule/capa/safe_exec/README.rst
        * remote setup (using Tutor): https://github.com/eduNEXT/tutor-contrib-codejail

        Note on @skip_unless_lms:
        This test can also be run in a CMS context, but that's giving us trouble in CI right now (the skip logic isn't
        working). So, if you're running this locally, feel free to remove @skip_unless_lms and run it against CMS too.
        '''
        # If in-platform codejail isn't configured...
        if not jail_code.is_configured("python"):

            # ...AND if remote codejail isn't configured...
            if not is_codejail_rest_service_enabled():

                # ...then skip this test.
                pytest.skip(reason="Local or remote codejail has to be configured and enabled to run this test.")

        g = {}
        with pytest.raises(SafeExecException) as cm:
            safe_exec('import sys; sys.exit(1)', g)
        assert "SystemExit" not in str(cm)
        assert "Couldn't execute jailed code" in str(cm)

    def test_can_do_something_forbidden_if_run_unsafely(self):
        '''
        Demonstrates that running unsafe code outside the code jail
        can cause issues directly in the calling process.
        '''
        g = {}
        with pytest.raises(SystemExit) as cm:
            safe_exec('import sys; sys.exit(1)', g, unsafely=True)
        assert "SystemExit" in str(cm)


class TestCodeJailDarkLaunch(unittest.TestCase):
    """
    Test that the behavior of the dark launched code behaves as expected.
    """
    @patch('xmodule.capa.safe_exec.safe_exec.get_remote_exec')
    @patch('xmodule.capa.safe_exec.safe_exec.codejail_safe_exec')
    def test_default_code_execution(self, mock_local_exec, mock_remote_exec):

        # Test default only runs local exec.
        g = {}
        safe_exec('a=1', g)
        assert mock_local_exec.called
        assert not mock_remote_exec.called

    @override_settings(ENABLE_CODEJAIL_REST_SERVICE=True)
    @patch('xmodule.capa.safe_exec.safe_exec.get_remote_exec')
    @patch('xmodule.capa.safe_exec.safe_exec.codejail_safe_exec')
    def test_code_execution_only_codejail_service(self, mock_local_exec, mock_remote_exec):
        # Set return values to empty values to indicate no error.
        mock_remote_exec.return_value = (None, None)
        # Test with only the service enabled.
        g = {}
        safe_exec('a=1', g)
        assert not mock_local_exec.called
        assert mock_remote_exec.called

    @override_settings(ENABLE_CODEJAIL_DARKLAUNCH=True)
    @patch('xmodule.capa.safe_exec.safe_exec.get_remote_exec')
    @patch('xmodule.capa.safe_exec.safe_exec.codejail_safe_exec')
    def test_code_execution_darklaunch_misconfig(self, mock_local_exec, mock_remote_exec):
        """Test that darklaunch doesn't run when remote service is generally enabled."""
        mock_remote_exec.return_value = (None, None)

        with override_settings(ENABLE_CODEJAIL_REST_SERVICE=True):
            safe_exec('a=1', {})

        assert not mock_local_exec.called
        assert mock_remote_exec.called

    @override_settings(ENABLE_CODEJAIL_DARKLAUNCH=True)
    def run_dark_launch(
            self, globals_dict, local, remote,
            expect_attr_calls, expect_log_info_calls, expect_globals_contains,
    ):
        """
        Run a darklaunch scenario with mocked out local and remote execution.

        Asserts set_custom_attribute and log.info calls and (partial) contents
        of globals dict.

        Return value is a dictionary of:

        - 'raised': Exception that safe_exec raised, or None.
        """

        assert is_codejail_in_darklaunch()

        with (
                patch('xmodule.capa.safe_exec.safe_exec.codejail_safe_exec') as mock_local_exec,
                patch('xmodule.capa.safe_exec.safe_exec.get_remote_exec') as mock_remote_exec,
                patch('xmodule.capa.safe_exec.safe_exec.set_custom_attribute') as mock_set_custom_attribute,
                patch('xmodule.capa.safe_exec.safe_exec.log.info') as mock_log_info,
        ):
            mock_local_exec.side_effect = local
            mock_remote_exec.side_effect = remote

            try:
                safe_exec(
                    "<IGNORED BY MOCKS>", globals_dict,
                    limit_overrides_context="course-v1:org+course+run", slug="hw1",
                )
            except BaseException as e:
                safe_exec_e = e
            else:
                safe_exec_e = None

        # Always want both sides to be called
        assert mock_local_exec.called
        assert mock_remote_exec.called

        mock_set_custom_attribute.assert_has_calls(expect_attr_calls, any_order=True)
        mock_log_info.assert_has_calls(expect_log_info_calls, any_order=True)

        for (k, v) in expect_globals_contains.items():
            assert globals_dict[k] == v

        return {'raised': safe_exec_e}

    # These don't change between the tests
    standard_codejail_attr_calls = [
        call('codejail.slug', 'hw1'),
        call('codejail.limit_overrides_context', 'course-v1:org+course+run'),
        call('codejail.extra_files_count', 0),
    ]

    def test_separate_globals(self):
        """Test that local and remote globals are isolated from each other's side effects."""
        # Both will attempt to read and write the 'overwrite' key.
        globals_dict = {'overwrite': 'original'}

        local_globals = None
        remote_globals = None

        def local_exec(code, globals_dict, **kwargs):
            # Preserve what local exec saw
            nonlocal local_globals
            local_globals = copy.deepcopy(globals_dict)

            globals_dict['overwrite'] = 'mock local'

        def remote_exec(data):
            # Preserve what remote exec saw
            nonlocal remote_globals
            remote_globals = copy.deepcopy(data['globals_dict'])

            data['globals_dict']['overwrite'] = 'mock remote'
            return (None, None)

        results = self.run_dark_launch(
            globals_dict=globals_dict, local=local_exec, remote=remote_exec,
            expect_attr_calls=[
                *self.standard_codejail_attr_calls,
                call('codejail.darklaunch.status.local', 'ok'),
                call('codejail.darklaunch.status.remote', 'ok'),
                call('codejail.darklaunch.exception.local', None),
                call('codejail.darklaunch.exception.remote', None),
                call('codejail.darklaunch.globals_match', False),  # mismatch revealed here
                call('codejail.darklaunch.emsg_match', True),
            ],
            expect_log_info_calls=[
                call(
                    "Codejail darklaunch had mismatch for "
                    "course='course-v1:org+course+run', slug='hw1':\n"
                    "emsg_match=True, globals_match=False\n"
                    "Local: globals={'overwrite': 'mock local'}, emsg=None\n"
                    "Remote: globals={'overwrite': 'mock remote'}, emsg=None"
                ),
            ],
            # Should only see behavior of local exec
            expect_globals_contains={'overwrite': 'mock local'},
        )
        assert results['raised'] is None

        # Both arms should have only seen the original globals object, untouched
        # by the other arm.
        assert local_globals == {'overwrite': 'original'}
        assert remote_globals == {'overwrite': 'original'}

    def test_remote_runs_even_if_local_raises(self):
        """Test that remote exec runs even if local raises."""
        def local_exec(code, globals_dict, **kwargs):
            # Raise something other than a SafeExecException.
            raise BaseException("unexpected")

        def remote_exec(data):
            return (None, None)

        results = self.run_dark_launch(
            globals_dict={}, local=local_exec, remote=remote_exec,
            expect_attr_calls=[
                *self.standard_codejail_attr_calls,
                call('codejail.darklaunch.status.local', 'unexpected_error'),
                call('codejail.darklaunch.status.remote', 'ok'),
                call('codejail.darklaunch.exception.local', "BaseException('unexpected')"),
                call('codejail.darklaunch.exception.remote', None),
                call('codejail.darklaunch.globals_match', "N/A"),
                call('codejail.darklaunch.emsg_match', "N/A"),
            ],
            expect_log_info_calls=[
                call(
                    "Codejail darklaunch had unexpected exception "
                    "for course='course-v1:org+course+run', slug='hw1':\n"
                    "Local exception: BaseException('unexpected')\n"
                    "Remote exception: None"
                ),
            ],
            expect_globals_contains={},
        )

        # Unexpected errors from local safe_exec propagate up.
        assert isinstance(results['raised'], BaseException)
        assert 'unexpected' in repr(results['raised'])

    def test_emsg_mismatch(self):
        """Test that local and remote error messages are compared."""
        def local_exec(code, globals_dict, **kwargs):
            raise SafeExecException("oops")

        def remote_exec(data):
            return ("OH NO", SafeExecException("OH NO"))

        results = self.run_dark_launch(
            globals_dict={}, local=local_exec, remote=remote_exec,
            expect_attr_calls=[
                *self.standard_codejail_attr_calls,
                call('codejail.darklaunch.status.local', 'safe_error'),
                call('codejail.darklaunch.status.remote', 'safe_error'),
                call('codejail.darklaunch.exception.local', None),
                call('codejail.darklaunch.exception.remote', None),
                call('codejail.darklaunch.globals_match', True),
                call('codejail.darklaunch.emsg_match', False),  # mismatch revealed here
            ],
            expect_log_info_calls=[
                call(
                    "Codejail darklaunch had mismatch for "
                    "course='course-v1:org+course+run', slug='hw1':\n"
                    "emsg_match=False, globals_match=True\n"
                    "Local: globals={}, emsg='oops'\n"
                    "Remote: globals={}, emsg='OH NO'"
                ),
            ],
            expect_globals_contains={},
        )
        assert isinstance(results['raised'], SafeExecException)
        assert 'oops' in repr(results['raised'])

    def test_ignore_sandbox_dir_mismatch(self):
        """Mismatch due only to differences in sandbox directory should be ignored."""
        def local_exec(code, globals_dict, **kwargs):
            raise SafeExecException("stack trace involving /tmp/codejail-1234567/whatever.py")

        def remote_exec(data):
            emsg = "stack trace involving /tmp/codejail-abcd_EFG/whatever.py"
            return (emsg, SafeExecException(emsg))

        results = self.run_dark_launch(
            globals_dict={}, local=local_exec, remote=remote_exec,
            expect_attr_calls=[
                *self.standard_codejail_attr_calls,
                call('codejail.darklaunch.status.local', 'safe_error'),
                call('codejail.darklaunch.status.remote', 'safe_error'),
                call('codejail.darklaunch.exception.local', None),
                call('codejail.darklaunch.exception.remote', None),
                call('codejail.darklaunch.globals_match', True),
                call('codejail.darklaunch.emsg_match', True),  # even though not exact match
            ],
            expect_log_info_calls=[],
            expect_globals_contains={},
        )
        assert isinstance(results['raised'], SafeExecException)
        assert 'whatever.py' in repr(results['raised'])

    def test_default_normalizers(self):
        """
        Default normalizers handle false mismatches we've observed.

        This just provides coverage for some of the more complicated patterns.
        """
        side_1 = (
            'Couldn\'t execute jailed code: stdout: b\'\', stderr: b\'Traceback'
            ' (most recent call last):\\n  File "/tmp/codejail-9g9715g_/jailed_code"'
            ', line 19, in <module>\\n    exec(code, g_dict)\\n  File "<string>"'
            ', line 1, in <module>\\n  File "<string>", line 89, in test_add\\n'
            '  File "<string>", line 1\\n    import random random.choice(range(10))'
            '\\n    ^\\nSyntaxError: invalid syntax\\n\' with status code: 1'
        )
        side_2 = (
            'Couldn\'t execute jailed code: stdout: b\'\', stderr: b\'Traceback'
            ' (most recent call last):\\n  File "jailed_code"'
            ', line 19, in <module>\\n    exec(code, g_dict)\\n  File "<string>"'
            ', line 203, in <module>\\n  File "<string>", line 89, in test_add\\n'
            '  File "<string>", line 1\\n    import random random.choice(range(10))'
            '\\n    ^^^^^^\\nSyntaxError: invalid syntax\\n\' with status code: 1'
        )
        assert normalize_error_message(side_1) == normalize_error_message(side_2)

    @override_settings(CODEJAIL_DARKLAUNCH_EMSG_NORMALIZERS=[
        {
            'search': r'[0-9]+',
            'replace': r'<NUM>',
        },
    ])
    def test_configurable_normalizers(self):
        """We can augment the normalizers, and they run in order."""
        emsg_in = "Error in /tmp/codejail-1234abcd/whatever.py: something 12 34 other"
        expect_out = "Error in /tmp/codejail-<SANDBOX_DIR_NAME>/whatever.py: something <NUM> <NUM> other"
        assert expect_out == normalize_error_message(emsg_in)

    @override_settings(
        CODEJAIL_DARKLAUNCH_EMSG_NORMALIZERS=[
            {
                'search': r'[0-9]+',
                'replace': r'<NUM>',
            },
        ],
        CODEJAIL_DARKLAUNCH_EMSG_NORMALIZERS_COMBINE='replace',
    )
    def test_can_replace_normalizers(self):
        """We can replace the normalizers."""
        emsg_in = "Error in /tmp/codejail-1234abcd/whatever.py: something 12 34 other"
        expect_out = "Error in /tmp/codejail-<NUM>abcd/whatever.py: something <NUM> <NUM> other"
        assert expect_out == normalize_error_message(emsg_in)

    @override_settings(CODEJAIL_DARKLAUNCH_EMSG_NORMALIZERS=[
        {
            'search': r'broken',
            'replace': r'replace \g<>',  # invalid replacement pattern
        },
    ])
    @patch('xmodule.capa.safe_exec.safe_exec.record_exception')
    @patch('xmodule.capa.safe_exec.safe_exec.log.error')
    def test_normalizers_validate(self, mock_log_error, mock_record_exception):
        """Normalizers are validated, and fall back to default list on error."""
        assert len(emsg_normalizers()) > 0  # pylint: disable=use-implicit-booleaness-not-comparison
        mock_log_error.assert_called_once_with(
            "Could not load custom codejail darklaunch emsg normalizers"
        )
        mock_record_exception.assert_called_once()


class TestLimitConfiguration(unittest.TestCase):
    """
    Test that resource limits can be configured and overriden via Django settings.

    We just test that the limits passed to `codejail` as we expect them to be.
    Actual resource limiting tests are within the `codejail` package itself.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Make a copy of codejail settings just for this test class.
        # Set a global REALTIME limit of 100.
        # Set a REALTIME limit override of 200 for a special course.
        cls.test_codejail_settings = (getattr(settings, 'CODE_JAIL', None) or {}).copy()
        cls.test_codejail_settings['limits'] = {
            'REALTIME': 100,
        }
        cls.test_codejail_settings['limit_overrides'] = {
            'course-v1:my+special+course': {'REALTIME': 200, 'NPROC': 30},
        }
        cls.configure_codejail(cls.test_codejail_settings)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

        # Re-apply original configuration.
        cls.configure_codejail(getattr(settings, 'CODE_JAIL', None) or {})

    @staticmethod
    def configure_codejail(codejail_settings):
        """
        Given a `settings.CODE_JAIL` dictionary, apply it to the codejail package.

        We use the `ConfigureCodeJailMiddleware` that comes with codejail.
        """
        with override_settings(CODE_JAIL=codejail_settings):
            # To apply `settings.CODE_JAIL`, we just intialize an instance of the
            # middleware class. We expect it to apply to changes, and then raise
            # "MiddlewareNotUsed" to indicate that its work is done.
            # This is exactly how the settings are applied in production (except the
            # middleware is automatically initialized because it's an element of
            # `settings.MIDDLEWARE`).
            try:
                ConfigureCodeJailMiddleware(get_response=lambda request: None)
            except MiddlewareNotUsed:
                pass

    def test_effective_limits_reflect_configuration(self):
        """
        Test that `get_effective_limits` returns configured limits with overrides
        applied correctly.
        """
        # REALTIME has been configured with a global limit.
        # Check it with no overrides context.
        assert jail_code.get_effective_limits()['REALTIME'] == 100

        # Now check REALTIME with an overrides context that we haven't configured.
        # Should be the same.
        assert jail_code.get_effective_limits('random-context-name')['REALTIME'] == 100

        # Now check REALTIME limit for a special course.
        # It should be overriden.
        assert jail_code.get_effective_limits('course-v1:my+special+course')['REALTIME'] == 200

        # We haven't configured a limit for NPROC.
        # It should use the codejail default.
        assert jail_code.get_effective_limits()['NPROC'] == 15

        # But we have configured an NPROC limit override for a special course.
        assert jail_code.get_effective_limits('course-v1:my+special+course')['NPROC'] == 30


class DictCache(object):
    """A cache implementation over a simple dict, for testing."""

    def __init__(self, d):
        self.cache = d

    def get(self, key):
        # Actual cache implementations have limits on key length
        assert len(key) <= 250
        return self.cache.get(key)

    def set(self, key, value):
        # Actual cache implementations have limits on key length
        assert len(key) <= 250
        self.cache[key] = value


@use_unsafe_codejail()
class TestSafeExecCaching(unittest.TestCase):
    """Test that caching works on safe_exec."""

    def test_cache_miss_then_hit(self):
        g = {}
        cache = {}

        # Cache miss
        safe_exec("a = int(math.pi)", g, cache=DictCache(cache))
        assert g['a'] == 3
        # A result has been cached
        assert list(cache.values())[0] == (None, {'a': 3})

        # Fiddle with the cache, then try it again.
        cache[list(cache.keys())[0]] = (None, {'a': 17})

        g = {}
        safe_exec("a = int(math.pi)", g, cache=DictCache(cache))
        assert g['a'] == 17

    def test_cache_large_code_chunk(self):
        # Caching used to die on memcache with more than 250 bytes of code.
        # Check that it doesn't any more.
        code = "a = 0\n" + ("a += 1\n" * 12345)

        g = {}
        cache = {}
        safe_exec(code, g, cache=DictCache(cache))
        assert g['a'] == 12345

    def test_cache_exceptions(self):
        # Used to be that running code that raised an exception didn't cache
        # the result.  Check that now it does.
        code = "1/0"
        g = {}
        cache = {}
        with pytest.raises(SafeExecException):
            safe_exec(code, g, cache=DictCache(cache))

        # The exception should be in the cache now.
        assert len(cache) == 1
        cache_exc_msg, cache_globals = list(cache.values())[0]  # lint-amnesty, pylint: disable=unused-variable
        assert 'ZeroDivisionError' in cache_exc_msg

        # Change the value stored in the cache, the result should change.
        cache[list(cache.keys())[0]] = ("Hey there!", {})

        with pytest.raises(SafeExecException):
            safe_exec(code, g, cache=DictCache(cache))

        assert len(cache) == 1
        cache_exc_msg, cache_globals = list(cache.values())[0]
        assert 'Hey there!' == cache_exc_msg

        # Change it again, now no exception!
        cache[list(cache.keys())[0]] = (None, {'a': 17})
        safe_exec(code, g, cache=DictCache(cache))
        assert g['a'] == 17

    def test_unicode_submission(self):
        # Check that using non-ASCII unicode does not raise an encoding error.
        # Try several non-ASCII unicode characters.
        for code in [129, 500, 2 ** 8 - 1, 2 ** 16 - 1]:
            code_with_unichr = str("# ") + unichr(code)
            try:
                safe_exec(code_with_unichr, {}, cache=DictCache({}))
            except UnicodeEncodeError:
                self.fail("Tried executing code with non-ASCII unicode: {0}".format(code))


class TestUpdateHash(unittest.TestCase):
    """Test the safe_exec.update_hash function to be sure it canonicalizes properly."""

    def hash_obj(self, obj):
        """Return the md5 hash that `update_hash` makes us."""
        md5er = hashlib.md5()
        update_hash(md5er, obj)
        return md5er.hexdigest()

    def equal_but_different_dicts(self):
        """
        Make two equal dicts with different key order.

        Simple literals won't do it.  Filling one and then shrinking it will
        make them different.

        """
        d1 = {k: 1 for k in "abcdefghijklmnopqrstuvwxyz"}
        d2 = {k: 1 for k in "bcdefghijklmnopqrstuvwxyza"}

        # Check that our dicts are equal, but with different key order.
        assert d1 == d2
        assert list(d1.keys()) != list(d2.keys())

        return d1, d2

    def test_simple_cases(self):
        h1 = self.hash_obj(1)
        h10 = self.hash_obj(10)
        hs1 = self.hash_obj("1")

        assert h1 != h10
        assert h1 != hs1

    def test_list_ordering(self):
        h1 = self.hash_obj({'a': [1, 2, 3]})
        h2 = self.hash_obj({'a': [3, 2, 1]})
        assert h1 != h2

    def test_dict_ordering(self):
        d1, d2 = self.equal_but_different_dicts()
        h1 = self.hash_obj(d1)
        h2 = self.hash_obj(d2)
        assert h1 == h2

    def test_deep_ordering(self):
        d1, d2 = self.equal_but_different_dicts()
        o1 = {'a': [1, 2, [d1], 3, 4]}
        o2 = {'a': [1, 2, [d2], 3, 4]}
        h1 = self.hash_obj(o1)
        h2 = self.hash_obj(o2)
        assert h1 == h2


@use_unsafe_codejail()
class TestRealProblems(unittest.TestCase):  # lint-amnesty, pylint: disable=missing-class-docstring
    def test_802x(self):
        code = textwrap.dedent("""\
            import math
            import random
            import numpy
            e=1.602e-19 #C
            me=9.1e-31  #kg
            mp=1.672e-27 #kg
            eps0=8.854e-12 #SI units
            mu0=4e-7*math.pi #SI units

            Rd1=random.randrange(1,30,1)
            Rd2=random.randrange(30,50,1)
            Rd3=random.randrange(50,70,1)
            Rd4=random.randrange(70,100,1)
            Rd5=random.randrange(100,120,1)

            Vd1=random.randrange(1,20,1)
            Vd2=random.randrange(20,40,1)
            Vd3=random.randrange(40,60,1)

            #R=[0,10,30,50,70,100] #Ohm
            #V=[0,12,24,36] # Volt

            R=[0,Rd1,Rd2,Rd3,Rd4,Rd5] #Ohms
            V=[0,Vd1,Vd2,Vd3] #Volts
            #here the currents IL and IR are defined as in figure ps3_p3_fig2
            a=numpy.array([  [  R[1]+R[4]+R[5],R[4] ],[R[4], R[2]+R[3]+R[4] ] ])
            b=numpy.array([V[1]-V[2],-V[3]-V[2]])
            x=numpy.linalg.solve(a,b)
            IL='%.2e' % x[0]
            IR='%.2e' % x[1]
            ILR='%.2e' % (x[0]+x[1])
            def sign(x):
                return abs(x)/x

            RW="Rightwards"
            LW="Leftwards"
            UW="Upwards"
            DW="Downwards"
            I1='%.2e' % abs(x[0])
            I1d=LW if sign(x[0])==1 else RW
            I1not=LW if I1d==RW else RW
            I2='%.2e' % abs(x[1])
            I2d=RW if sign(x[1])==1 else LW
            I2not=LW if I2d==RW else RW
            I3='%.2e' % abs(x[1])
            I3d=DW if sign(x[1])==1 else UW
            I3not=DW if I3d==UW else UW
            I4='%.2e' % abs(x[0]+x[1])
            I4d=UW if sign(x[1]+x[0])==1 else DW
            I4not=DW if I4d==UW else UW
            I5='%.2e' % abs(x[0])
            I5d=RW if sign(x[0])==1 else LW
            I5not=LW if I5d==RW else RW
            VAP=-x[0]*R[1]-(x[0]+x[1])*R[4]
            VPN=-V[2]
            VGD=+V[1]-x[0]*R[1]+V[3]+x[1]*R[2]
            aVAP='%.2e' % VAP
            aVPN='%.2e' % VPN
            aVGD='%.2e' % VGD
            """)
        g = {}
        safe_exec(code, g)
        assert 'aVAP' in g
