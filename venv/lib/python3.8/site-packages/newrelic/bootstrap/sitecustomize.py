# Copyright 2010 New Relic, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys
import time

# Define some debug logging routines to help sort out things when this
# all doesn't work as expected.


# Avoiding additional imports by defining PY2 manually
PY2 = sys.version_info[0] == 2

startup_debug = os.environ.get("NEW_RELIC_STARTUP_DEBUG", "off").lower() in ("on", "true", "1")


def log_message(text, *args, **kwargs):
    critical = kwargs.get("critical", False)
    if startup_debug or critical:
        text = text % args
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        sys.stdout.write("NEWRELIC: %s (%d) - %s\n" % (timestamp, os.getpid(), text))
        sys.stdout.flush()


log_message("New Relic Bootstrap (%s)", __file__)

log_message("working_directory = %r", os.getcwd())

log_message("sys.prefix = %r", os.path.normpath(sys.prefix))

try:
    log_message("sys.real_prefix = %r", sys.real_prefix)
except AttributeError:
    pass

log_message("sys.version_info = %r", sys.version_info)
log_message("sys.executable = %r", sys.executable)

if hasattr(sys, "flags"):
    log_message("sys.flags = %r", sys.flags)

log_message("sys.path = %r", sys.path)

for name in sorted(os.environ.keys()):
    if name.startswith("NEW_RELIC_") or name.startswith("PYTHON"):
        if name == "NEW_RELIC_LICENSE_KEY":
            continue
        log_message("%s = %r", name, os.environ.get(name))

# We need to import the original sitecustomize.py file if it exists. We
# can't just try and import the existing one as we will pick up
# ourselves again. Even if we remove ourselves from sys.modules and
# remove the bootstrap directory from sys.path, still not sure that the
# import system will not have cached something and return a reference to
# ourselves rather than searching again. What we therefore do is use the
# imp module to find the module, excluding the bootstrap directory from
# the search, and then load what was found.

boot_directory = os.path.dirname(__file__)
root_directory = os.path.dirname(os.path.dirname(boot_directory))

log_message("root_directory = %r", root_directory)
log_message("boot_directory = %r", boot_directory)

path = list(sys.path)

if boot_directory in path:
    del path[path.index(boot_directory)]

try:
    if PY2:
        import imp

        module_spec = imp.find_module("sitecustomize", path)
    else:
        from importlib.machinery import PathFinder

        module_spec = PathFinder.find_spec("sitecustomize", path=path)

except ImportError:
    pass
else:
    if module_spec is not None:  # Import error not raised in importlib
        log_message("sitecustomize = %r", module_spec)

        if PY2:
            imp.load_module("sitecustomize", *module_spec)
        else:
            module_spec.loader.load_module("sitecustomize")

# Because the PYTHONPATH environment variable has been amended and the
# bootstrap directory added, if a Python application creates a sub
# process which runs a different Python interpreter, then it will still
# load this sitecustomize.py. If that is for a different Python version
# it will cause problems if we then try and import and initialize the
# agent. We therefore need to try our best to verify that we are running
# in the same Python installation as the original newrelic-admin script
# which was run and only continue if we are.

expected_python_prefix = os.environ.get("NEW_RELIC_PYTHON_PREFIX")
actual_python_prefix = os.path.realpath(os.path.normpath(sys.prefix))

expected_python_version = os.environ.get("NEW_RELIC_PYTHON_VERSION")
actual_python_version = ".".join(map(str, sys.version_info[:2]))

python_prefix_matches = expected_python_prefix == actual_python_prefix
python_version_matches = expected_python_version == actual_python_version

log_message("python_prefix_matches = %r", python_prefix_matches)
log_message("python_version_matches = %r", python_version_matches)

if python_prefix_matches and python_version_matches:
    # We also need to skip agent initialisation if neither the license
    # key or config file environment variables are set. We do this as
    # some people like to use a common startup script which always uses
    # the wrapper script, and which controls whether the agent is
    # actually run based on the presence of the environment variables.

    license_key = os.environ.get("NEW_RELIC_LICENSE_KEY", None)

    config_file = os.environ.get("NEW_RELIC_CONFIG_FILE", None)
    environment = os.environ.get("NEW_RELIC_ENVIRONMENT", None)

    log_message("initialize_agent = %r", bool(license_key or config_file))

    if license_key or config_file:
        # When installed as an egg with buildout, the root directory for
        # packages is not listed in sys.path and scripts instead set it
        # after Python has started up. This will cause importing of
        # 'newrelic' module to fail. What we do is see if the root
        # directory where the package is held is in sys.path and if not
        # insert it. For good measure we remove it after having imported
        # 'newrelic' module to reduce chance that will cause any issues.
        # If it is a buildout created script, it will replace the whole
        # sys.path again later anyway.

        do_insert_path = root_directory not in sys.path
        if do_insert_path:
            sys.path.insert(0, root_directory)

        import newrelic.config

        log_message("agent_version = %r", newrelic.version)

        if do_insert_path:
            try:
                del sys.path[sys.path.index(root_directory)]
            except Exception:
                pass

        # Finally initialize the agent.

        newrelic.config.initialize(config_file, environment)
else:
    log_message(
        """New Relic could not start because the newrelic-admin script was called from a Python installation that is different from the Python installation that is currently running. To fix this problem, call the newrelic-admin script from the Python installation that is currently running (details below).

newrelic-admin Python directory: %r
current Python directory: %r
newrelic-admin Python version: %r
current Python version: %r""",
        expected_python_prefix,
        actual_python_prefix,
        expected_python_version,
        actual_python_version,
        critical=True,
    )
