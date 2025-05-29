"""Capa's specialized use of codejail.safe_exec."""
import copy
import hashlib
import logging
import re
from functools import lru_cache
from typing import assert_type

from codejail.safe_exec import SafeExecException, json_safe
from codejail.safe_exec import not_safe_exec as codejail_not_safe_exec
from codejail.safe_exec import safe_exec as codejail_safe_exec
from django.conf import settings
from django.dispatch import receiver
from django.test.signals import setting_changed
from edx_django_utils.monitoring import function_trace, record_exception, set_custom_attribute

from . import lazymod
from .remote_exec import get_remote_exec, is_codejail_in_darklaunch, is_codejail_rest_service_enabled

log = logging.getLogger(__name__)


# Establish the Python environment for Capa.
# Capa assumes float-friendly division always.
# The name "random" is a properly-seeded stand-in for the random module.
CODE_PROLOG = """\
from __future__ import absolute_import, division

import os

# openblas is a math library used by numpy. It will try to allocate multiple
# threads by default, but this may exceed resource limits and cause a segfault.
# Limiting to 1 thread will prevent this in all configurations.
os.environ["OPENBLAS_NUM_THREADS"] = "1"

# Any code that uses the tempfile module to create temporary files should use
# the ./tmp directory that codejail creates in each sandbox, rather than trying
# to use a global temp dir (which should be blocked by AppArmor anyhow).
# This is needed for matplotlib among other things.
#
# matplotlib will complain on stderr about the non-standard temp dir if we
# don't explicitly tell it "no really, use this". This pollutes the output
# when codejail returns an error message (which includes stderr). So we also
# set MPLCONFIGDIR as a special case.
os.environ["TMPDIR"] = os.getcwd() + "/tmp"
os.environ["MPLCONFIGDIR"] = os.environ["TMPDIR"]

import random2 as random_module
import sys
from six.moves import xrange

random = random_module.Random(%r)
random.Random = random_module.Random
random.SystemRandom = random_module.SystemRandom
sys.modules['random'] = random
"""

ASSUMED_IMPORTS = [
    ("numpy", "numpy"),
    ("math", "math"),
    ("scipy", "scipy"),
    ("calc", "calc"),
    ("eia", "eia"),
    ("chemcalc", "chem.chemcalc"),
    ("chemtools", "chem.chemtools"),
    ("miller", "chem.miller"),
    ("draganddrop", "verifiers.draganddrop"),
]

# We'll need the code from lazymod.py for use in safe_exec, so read it now.
lazymod_py_file = lazymod.__file__
if lazymod_py_file.endswith("c"):
    lazymod_py_file = lazymod_py_file[:-1]

with open(lazymod_py_file) as f:
    lazymod_py = f.read()

LAZY_IMPORTS = [lazymod_py]
for name, modname in ASSUMED_IMPORTS:
    LAZY_IMPORTS.append("{} = LazyModule('{}')\n".format(name, modname))

LAZY_IMPORTS = "".join(LAZY_IMPORTS)


def update_hash(hasher, obj):
    """
    Update a `hashlib` hasher with a nested object.

    To properly cache nested structures, we need to compute a hash from the
    entire structure, canonicalizing at every level.

    `hasher`'s `.update()` method is called a number of times, touching all of
    `obj` in the process.  Only primitive JSON-safe types are supported.

    """
    hasher.update(str(type(obj)).encode())
    if isinstance(obj, (tuple, list)):
        for e in obj:
            update_hash(hasher, e)
    elif isinstance(obj, dict):
        for k in sorted(obj):
            update_hash(hasher, k)
            update_hash(hasher, obj[k])
    else:
        hasher.update(repr(obj).encode())


@function_trace('safe_exec')
def safe_exec(
    code,
    globals_dict,
    random_seed=None,
    python_path=None,
    extra_files=None,
    cache=None,
    limit_overrides_context=None,
    slug=None,
    unsafely=False,
):  # pylint: disable=too-many-statements
    """
    Execute python code safely.

    `code` is the Python code to execute.  It has access to the globals in `globals_dict`,
    and any changes it makes to those globals are visible in `globals_dict` when this
    function returns.

    `random_seed` will be used to see the `random` module available to the code.

    `python_path` is a list of filenames or directories to add to the Python
    path before execution.  If the name is not in `extra_files`, then it will
    also be copied into the sandbox.

    `extra_files` is a list of (filename, contents) pairs.  These files are
    created in the sandbox.

    `cache` is an object with .get(key) and .set(key, value) methods.  It will be used
    to cache the execution, taking into account the code, the values of the globals,
    and the random seed.

    `limit_overrides_context` is an optional string to be used as a key on
    the `settings.CODE_JAIL['limit_overrides']` dictionary in order to apply
    context-specific overrides to the codejail execution limits.
    If `limit_overrides_context` is omitted or not present in limit_overrides,
    then use the default limits specified insettings.CODE_JAIL['limits'].

    `slug` is an arbitrary string, a description that's meaningful to the
    caller, that will be used in log messages.

    If `unsafely` is true, then the code will actually be executed without sandboxing.
    """
    # Check the cache for a previous result.
    if cache:
        safe_globals = json_safe(globals_dict)
        md5er = hashlib.md5()
        md5er.update(repr(code).encode('utf-8'))
        update_hash(md5er, safe_globals)
        key = "safe_exec.%r.%s" % (random_seed, md5er.hexdigest())
        cached = cache.get(key)
        if cached is not None:
            # We have a cached result.  The result is a pair: the exception
            # message, if any, else None; and the resulting globals dictionary.
            emsg, cleaned_results = cached
            globals_dict.update(cleaned_results)
            if emsg:
                raise SafeExecException(emsg)
            return

    cacheable = True  # unless we get an unexpected error

    # Create the complete code we'll run.
    code_prolog = CODE_PROLOG % random_seed

    if is_codejail_rest_service_enabled():
        data = {
            "code": code_prolog + LAZY_IMPORTS + code,
            "globals_dict": globals_dict,
            "python_path": python_path,
            "limit_overrides_context": limit_overrides_context,
            "slug": slug,
            "unsafely": unsafely,
            "extra_files": extra_files,
        }

        with function_trace('safe_exec.remote_exec'):
            emsg, exception = get_remote_exec(data)

    else:

        # Create a copy so the originals are not modified as part of this call.
        # This has to happen before local exec is run, since globals are modified
        # as a side effect.
        darklaunch_globals = copy.deepcopy(globals_dict)

        # Decide which code executor to use.
        if unsafely:
            exec_fn = codejail_not_safe_exec
        else:
            exec_fn = codejail_safe_exec

        # Run the code!  Results are side effects in globals_dict.
        try:
            trace_name = 'safe_exec.local_exec_darklaunch' if is_codejail_in_darklaunch() else 'safe_exec.local_exec'
            with function_trace(trace_name):
                exec_fn(
                    code_prolog + LAZY_IMPORTS + code,
                    globals_dict,
                    python_path=python_path,
                    extra_files=extra_files,
                    limit_overrides_context=limit_overrides_context,
                    slug=slug,
                )
        except BaseException as e:
            # Saving SafeExecException e in exception to be used later.
            exception = e
            emsg = str(e)
            if not isinstance(exception, SafeExecException):
                # Something unexpected happened, so don't cache this evaluation.
                # (We may decide to cache these in the future as well; this is just
                # preserving existing behavior during a refactor of error handling.)
                cacheable = False
        else:
            exception = None
            emsg = None

        # Run the code in both the remote codejail service as well as the local codejail
        # when in darklaunch mode.
        if is_codejail_in_darklaunch():
            # Start adding attributes only once we're in a darklaunch
            # comparison, even though these particular ones aren't specific to
            # darklaunch. There can be multiple codejail calls per trace, and
            # these attrs will overwrite previous values in the same trace. When
            # that happens, we need to ensure we overwrite *all* of them,
            # otherwise we could end up with inconsistent combinations of values.

            # .. custom_attribute_name: codejail.slug
            # .. custom_attribute_description: Value of the slug parameter. This
            #   might be a problem ID, if present.
            set_custom_attribute('codejail.slug', slug)
            # .. custom_attribute_name: codejail.limit_overrides_context
            # .. custom_attribute_description: Value of the limit_overrides_context
            #   parameter to this code execution. Generally this will be the
            #   course name, if present at all.
            set_custom_attribute('codejail.limit_overrides_context', limit_overrides_context)
            # .. custom_attribute_name: codejail.extra_files_count
            # .. custom_attribute_description: Number of extra_files included
            #   in request. This should be 0 or 1, the latter indicating a
            #   python_lib.zip was present.
            set_custom_attribute('codejail.extra_files_count', len(extra_files) if extra_files else 0)

            try:
                data = {
                    "code": code_prolog + LAZY_IMPORTS + code,
                    "globals_dict": darklaunch_globals,
                    "python_path": python_path,
                    "limit_overrides_context": limit_overrides_context,
                    "slug": slug,
                    "unsafely": unsafely,
                    "extra_files": extra_files,
                }
                with function_trace('safe_exec.remote_exec_darklaunch'):
                    # Ignore the returned exception, because it's just a
                    # SafeExecException wrapped around emsg (if present).
                    remote_emsg, _ = get_remote_exec(data)
                    remote_exception = None
            except BaseException as e:  # pragma: no cover  # pylint: disable=broad-except
                # Swallow all exceptions and log it in monitoring so that dark launch doesn't cause issues during
                # deploy.
                remote_emsg = None
                remote_exception = e

            try:
                local_exc_unexpected = None if isinstance(exception, SafeExecException) else exception

                report_darklaunch_results(
                    limit_overrides_context=limit_overrides_context, slug=slug,
                    globals_local=globals_dict, emsg_local=emsg, unexpected_exc_local=local_exc_unexpected,
                    globals_remote=darklaunch_globals, emsg_remote=remote_emsg, unexpected_exc_remote=remote_exception,
                )
            except BaseException as e:  # pragma: no cover  # pylint: disable=broad-except
                log.exception("Error occurred while trying to report codejail darklaunch data.")
                record_exception()

    # Put the result back in the cache.  This is complicated by the fact that
    # the globals dict might not be entirely serializable.
    if cache and cacheable:
        cleaned_results = json_safe(globals_dict)
        cache.set(key, (emsg, cleaned_results))

    # If an exception happened, raise it now.
    if exception:
        raise exception


def _compile_normalizers(normalizer_setting):
    """
    Compile emsg normalizer search/replace pairs into regex.

    Raises exception on bad settings.
    """
    compiled = []
    for pair in normalizer_setting:
        search = re.compile(assert_type(pair['search'], str))
        replace = assert_type(pair['replace'], str)

        # Test the replacement string (might contain errors)
        re.sub(search, replace, "example")

        compiled.append({'search': search, 'replace': replace})
    return compiled


@lru_cache(maxsize=1)
def emsg_normalizers():
    """
    Load emsg normalization settings.

    The output is like the setting value, except the 'search' patterns have
    been compiled.
    """
    default_setting = [
        {
            # Character range should be at least as broad as what Python's `tempfile` uses.
            'search': r'/tmp/codejail-[0-9a-zA-Z_]+',
            'replace': r'/tmp/codejail-<SANDBOX_DIR_NAME>',
        },

        # These are useful for eliding differences in environments due to Python version:

        {
            # Python 3.8 doesn't include the dir here, but Python 3.12
            # does. Normalize to the 3.8 version.
            'search': r'File "/tmp/codejail-<SANDBOX_DIR_NAME>/jailed_code"',
            'replace': r'File "jailed_code"'
        },
        {
            # Python version shows up in stack traces in the virtualenv paths
            'search': r'python3\.[0-9]+',
            'replace': r'python3.XX'
        },
        {
            # Line numbers in stack traces differ between Python versions
            'search': r', line [0-9]+, in ',
            'replace': r', line XXX, in '
        },
        {
            # Some time after 3.8, Python started adding '^^^' indicators to stack traces
            'search': r'\\n\s*\^+\s*\\n',
            'replace': r'\\n'
        },
        {
            # Python3.8 had these <listcomp> stack trace elements but 3.12 does not
            'search': r'\\n  File "[^"]+", line [0-9]+, in <listcomp>\\n',
            'replace': r'\\n'
        },
    ]
    default_normalizers = _compile_normalizers(default_setting)

    # .. setting_name: CODEJAIL_DARKLAUNCH_EMSG_NORMALIZERS
    # .. setting_default: []
    # .. setting_description: A list of patterns to search and replace in codejail error
    #   messages during comparison in codejail-service darklaunch. Each entry is a dict
    #   of 'search' (a regular expression string) and 'replace' (the replacement string).
    #   Deployers may also need to add a search/replace pair for the location of the sandbox
    #   virtualenv, or any other paths that show up in stack traces.
    # .. setting_warning: Note that `replace' is a pattern, allowing for
    #   backreferences. Any backslashes in the replacement pattern that are not
    #   intended as backreferences should be escaped as `\\`.
    #   The default list suppresses differences due to the randomly-named sandboxes
    #   or to differences due to Python version. See setting
    #   ``CODEJAIL_DARKLAUNCH_EMSG_NORMALIZERS_COMBINE`` for information on how
    #   this setting interacts with the defaults.
    custom_setting = getattr(settings, 'CODEJAIL_DARKLAUNCH_EMSG_NORMALIZERS', [])
    try:
        custom_normalizers = _compile_normalizers(custom_setting)
    except BaseException as e:
        log.error("Could not load custom codejail darklaunch emsg normalizers")
        record_exception()
        return default_normalizers

    # .. setting_name: CODEJAIL_DARKLAUNCH_EMSG_NORMALIZERS_COMBINE
    # .. setting_default: 'append'
    # .. setting_description: How to combine ``CODEJAIL_DARKLAUNCH_EMSG_NORMALIZERS``
    #   with the defaults. If the value is 'replace', the defaults will be replaced
    #   with the specified patterns. If the value is 'append' (the default), the
    #   specified replacements will be run after the defaults.
    combine = getattr(settings, 'CODEJAIL_DARKLAUNCH_EMSG_NORMALIZERS_COMBINE', 'append')
    if combine == 'replace':
        return custom_normalizers
    else:  # 'append', or unknown
        return default_normalizers + custom_normalizers


def normalize_error_message(emsg):
    """
    Remove any uninteresting sources of discrepancy from an emsg.
    """
    if emsg is None:
        return None

    for replacer in emsg_normalizers():
        emsg = re.sub(replacer['search'], replacer['replace'], emsg, count=0)

    return emsg


def report_darklaunch_results(
        *, limit_overrides_context, slug,
        globals_local, emsg_local, unexpected_exc_local,
        globals_remote, emsg_remote, unexpected_exc_remote,
):
    """Send telemetry for results of darklaunch."""
    can_compare_output = True

    def report_arm(arm, emsg, unexpected_exception):
        """
        Set custom attributes for each arm of the darklaunch experiment.

        `arm` should be 'local' or 'remote'.
        """
        nonlocal can_compare_output
        if unexpected_exception:
            # .. custom_attribute_name: codejail.darklaunch.status.{local,remote}
            # .. custom_attribute_description: Outcome of this arm of the
            #   darklaunch comparison. Values can be 'ok' (normal execution),
            #   'safe_error' (submitted code raised an exception), or
            #   'unexpected_error' (uncaught error in submitting or evaluating code).
            set_custom_attribute(f'codejail.darklaunch.status.{arm}', 'unexpected_error')
            # .. custom_attribute_name: codejail.darklaunch.exception.{local,remote}
            # .. custom_attribute_description: When the status attribute indicates
            #   an unexpected error, this is a string representation of the error,
            #   otherwise None.
            set_custom_attribute(f'codejail.darklaunch.exception.{arm}', repr(unexpected_exception))
            can_compare_output = False
        else:
            set_custom_attribute(f'codejail.darklaunch.status.{arm}', 'ok' if emsg is None else 'safe_error')
            set_custom_attribute(f'codejail.darklaunch.exception.{arm}', None)

    report_arm('local', emsg_local, unexpected_exc_local)
    report_arm('remote', emsg_remote, unexpected_exc_remote)

    # If the arms can't be compared (unexpected errors), stop early -- the rest
    # is about output comparison.
    if not can_compare_output:
        set_custom_attribute('codejail.darklaunch.globals_match', 'N/A')
        set_custom_attribute('codejail.darklaunch.emsg_match', 'N/A')
        log.info(
            "Codejail darklaunch had unexpected exception for "
            f"course={limit_overrides_context!r}, slug={slug!r}:\n"
            f"Local exception: {unexpected_exc_local!r}\n"
            f"Remote exception: {unexpected_exc_remote!r}"
        )
        return

    globals_match = globals_local == globals_remote
    emsg_match = normalize_error_message(emsg_local) == normalize_error_message(emsg_remote)

    if not globals_match or not emsg_match:
        log.info(
            f"Codejail darklaunch had mismatch for course={limit_overrides_context!r}, slug={slug!r}:\n"
            f"{emsg_match=}, {globals_match=}\n"
            f"Local: globals={globals_local!r}, emsg={emsg_local!r}\n"
            f"Remote: globals={globals_remote!r}, emsg={emsg_remote!r}"
        )

    # .. custom_attribute_name: codejail.darklaunch.globals_match
    # .. custom_attribute_description: True if local and remote globals_dict
    #   values match, False otherwise. 'N/A' when either arm raised an
    #   uncaught error.
    set_custom_attribute('codejail.darklaunch.globals_match', globals_match)
    # .. custom_attribute_name: codejail.darklaunch.emsg_match
    # .. custom_attribute_description: True if the local and remote emsg values
    #   (errors returned from sandbox) match, False otherwise. Differences due
    #   to known irrelevant factors are suppressed in this comparison, such as
    #   the randomized directory names used for sandboxes. 'N/A' when either
    #   arm raised an uncaught error.
    set_custom_attribute('codejail.darklaunch.emsg_match', emsg_match)


@receiver(setting_changed)
def reset_caches(sender, **kwargs):
    """
    Reset cached settings during unit tests.
    """
    emsg_normalizers.cache_clear()
