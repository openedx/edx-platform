"""Safe execution of untrusted Python code."""

import json
import logging
import os.path
import shutil
import sys
import textwrap

from codejail import jailpy
from codejail.util import temp_directory, change_directory

log = logging.getLogger(__name__)


def safe_exec(code, globals_dict, files=None, python_path=None):
    """Execute code as "exec" does, but safely.

    `code` is a string of Python code.  `globals_dict` is used as the globals
    during execution.  Modifications the code makes to `globals_dict` are
    reflected in the dictionary on return.

    Returns None.  Changes made by `code` are visible in `globals_dict`.

    """
    the_code = []
    files = list(files or ())

    the_code.append(textwrap.dedent(
        """
        import json
        import sys
        """
        # We need to prevent the sandboxed code from printing to stdout,
        # or it will pollute the json we print there.  This isn't a
        # security concern (they can put any values in the json output
        # anyway, either by writing to sys.__stdout__, or just by defining
        # global values), but keeps accidents from happening.
        """
        class DevNull(object):
            def write(self, *args, **kwargs):
                pass
        sys.stdout = DevNull()
        """
        # Read the code and the globals from the stdin.
        """
        code, g_dict = json.load(sys.stdin)
        """))

    for pydir in python_path or ():
        pybase = os.path.basename(pydir)
        the_code.append("sys.path.append(%r)\n" % pybase)
        files.append(pydir)

    the_code.append(textwrap.dedent(
        # Execute the sandboxed code.
        """
        exec code in g_dict
        """
        # Clean the globals for sending back as JSON over stdout.
        """
        ok_types = (type(None), int, long, float, str, unicode, list, tuple, dict)
        bad_keys = ("__builtins__",)
        def jsonable(v):
            if not isinstance(v, ok_types):
                return False
            try:
                json.dumps(v)
            except Exception:
                return False
            return True
        g_dict = {k:v for k,v in g_dict.iteritems() if jsonable(v) and k not in bad_keys}
        """
        # Write the globals back to the calling process.
        """
        json.dump(g_dict, sys.__stdout__)
        """))

    stdin = json.dumps([code, json_safe(globals_dict)])
    jailed_code = "".join(the_code)

    # Turn this on to see what's being executed.
    if 0:
        log.debug("Jailed code: %s", jailed_code)
        log.debug("Exec: %s", code)
        log.debug("Stdin: %s", stdin)

    res = jailpy.jailpy(jailed_code, stdin=stdin, files=files)
    if res.status != 0:
        raise Exception("Couldn't execute jailed code: %s" % res.stderr)
    globals_dict.update(json.loads(res.stdout))


def json_safe(d):
    """Return only the JSON-safe part of d.

    Used to emulate reading data through a serialization straw.

    """
    ok_types = (type(None), int, long, float, str, unicode, list, tuple, dict)
    bad_keys = ("__builtins__",)
    jd = {}
    for k, v in d.iteritems():
        if not isinstance(v, ok_types):
            continue
        if k in bad_keys:
            continue
        try:
            json.dumps(v)
        except TypeError:
            continue
        else:
            jd[k] = v
    return json.loads(json.dumps(jd))


def not_safe_exec(code, globals_dict, files=None, python_path=None):
    """Another implementation of `safe_exec`, but not safe.

    This can be swapped in for debugging problems in sandboxed Python code.

    This is not thread-safe, due to temporarily changing the current directory
    and modifying sys.path.

    """
    g_dict = json_safe(globals_dict)

    with temp_directory(delete_when_done=True) as tmpdir:
        with change_directory(tmpdir):
            # Copy the files here.
            for filename in files or ():
                dest = os.path.join(tmpdir, os.path.basename(filename))
                shutil.copyfile(filename, dest)

            original_path = sys.path
            if python_path:
                sys.path.extend(python_path)
            try:
                exec code in g_dict
            finally:
                sys.path = original_path

    globals_dict.update(json_safe(g_dict))

# Running Python code in the sandbox makes it difficult to debug.
# Change 0 to 1 to run the code directly.
if 0 or not jailpy.is_configured():
    safe_exec = not_safe_exec
