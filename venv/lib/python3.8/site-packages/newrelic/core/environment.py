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

"""This module provides functions to collect information about the operating
system, Python and hosting environment.

"""

import newrelic

from newrelic.common.system_info import (total_physical_memory,
    logical_processor_count, physical_processor_count)

import sys
import os
import platform

# try:
#     import pkg_resources
# except ImportError:
#     pass

try:
    import newrelic.core._thread_utilization
except ImportError:
    pass


def environment_settings():
    """Returns an array of arrays of environment settings

    """

    env = []

    # Agent information.

    env.append(('Agent Version', '.'.join(map(str, newrelic.version_info))))

    # System information.

    env.append(('Arch', platform.machine()))
    env.append(('OS', platform.system()))
    env.append(('OS version', platform.release()))

    env.append(('Total Physical Memory (MB)', total_physical_memory()))
    env.append(('Logical Processors', logical_processor_count()))

    physical_processor_packages, physical_cores = physical_processor_count()

    # Report this attribute only if it has a valid value.

    if physical_processor_packages:
        env.append(('Physical Processor Packages',
            physical_processor_packages))

    # Report this attribute only if it has a valid value.

    if physical_cores:
        env.append(('Physical Cores', physical_cores))

    # Python information.

    env.append(('Python Program Name', sys.argv[0]))

    env.append(('Python Executable', sys.executable))

    env.append(('Python Home', os.environ.get('PYTHONHOME', '')))
    env.append(('Python Path', os.environ.get('PYTHONPATH', '')))

    env.append(('Python Prefix', sys.prefix))
    env.append(('Python Exec Prefix', sys.exec_prefix))

    env.append(('Python Runtime', '.'.join(platform.python_version_tuple())))

    env.append(('Python Implementation', platform.python_implementation()))
    env.append(('Python Version', sys.version))

    env.append(('Python Platform', sys.platform))

    env.append(('Python Max Unicode', sys.maxunicode))

    # Extensions information.

    extensions = []

    if 'newrelic.core._thread_utilization' in sys.modules:
        extensions.append('newrelic.core._thread_utilization')

    env.append(('Compiled Extensions', ', '.join(extensions)))

    # Dispatcher information.

    dispatcher = []

    if not dispatcher and 'mod_wsgi' in sys.modules:
        mod_wsgi = sys.modules['mod_wsgi']
        if hasattr(mod_wsgi, 'process_group'):
            if mod_wsgi.process_group == '':
                dispatcher.append(('Dispatcher', 'Apache/mod_wsgi (embedded)'))
            else:
                dispatcher.append(('Dispatcher', 'Apache/mod_wsgi (daemon)'))
            env.append(('Apache/mod_wsgi Process Group',
                    mod_wsgi.process_group))
        else:
            dispatcher.append(('Dispatcher', 'Apache/mod_wsgi'))
        if hasattr(mod_wsgi, 'version'):
            dispatcher.append(('Dispatcher Version', str(mod_wsgi.version)))
        if hasattr(mod_wsgi, 'application_group'):
            env.append(('Apache/mod_wsgi Application Group',
                    mod_wsgi.application_group))

    if not dispatcher and 'uwsgi' in sys.modules:
        dispatcher.append(('Dispatcher', 'uWSGI'))
        uwsgi = sys.modules['uwsgi']
        if hasattr(uwsgi, 'version'):
            dispatcher.append(('Dispatcher Version', uwsgi.version))

    if not dispatcher and 'flup.server.fcgi' in sys.modules:
        dispatcher.append(('Dispatcher', 'flup/fastcgi (threaded)'))

    if not dispatcher and 'flup.server.fcgi_fork' in sys.modules:
        dispatcher.append(('Dispatcher', 'flup/fastcgi (prefork)'))

    if not dispatcher and 'flup.server.scgi' in sys.modules:
        dispatcher.append(('Dispatcher', 'flup/scgi (threaded)'))

    if not dispatcher and 'flup.server.scgi_fork' in sys.modules:
        dispatcher.append(('Dispatcher', 'flup/scgi (prefork)'))

    if not dispatcher and 'flup.server.ajp' in sys.modules:
        dispatcher.append(('Dispatcher', 'flup/ajp (threaded)'))

    if not dispatcher and 'flup.server.ajp_fork' in sys.modules:
        dispatcher.append(('Dispatcher', 'flup/ajp (forking)'))

    if not dispatcher and 'flup.server.cgi' in sys.modules:
        dispatcher.append(('Dispatcher', 'flup/cgi'))

    if not dispatcher and 'gunicorn' in sys.modules:
        if 'gunicorn.workers.ggevent' in sys.modules:
            dispatcher.append(('Dispatcher', 'gunicorn (gevent)'))
        elif 'gunicorn.workers.geventlet' in sys.modules:
            dispatcher.append(('Dispatcher', 'gunicorn (eventlet)'))
        elif 'uvicorn.workers' in sys.modules:
            dispatcher.append(('Dispatcher', 'gunicorn (uvicorn)'))
            uvicorn = sys.modules.get('uvicorn')
            if hasattr(uvicorn, '__version__'):
                dispatcher.append(('Worker Version', uvicorn.__version__))
        else:
            dispatcher.append(('Dispatcher', 'gunicorn'))

        gunicorn = sys.modules['gunicorn']
        if hasattr(gunicorn, '__version__'):
            dispatcher.append(('Dispatcher Version', gunicorn.__version__))

    if not dispatcher and 'uvicorn' in sys.modules:
        dispatcher.append(('Dispatcher', 'uvicorn'))
        uvicorn = sys.modules['uvicorn']

        if hasattr(uvicorn, '__version__'):
            dispatcher.append(('Dispatcher Version', uvicorn.__version__))

    if not dispatcher and 'tornado' in sys.modules:
        dispatcher.append(('Dispatcher', 'tornado'))
        tornado = sys.modules['tornado']
        if hasattr(tornado, 'version_info'):
            dispatcher.append(('Dispatcher Version',
                               str(tornado.version_info)))

    env.extend(dispatcher)

    # Module information.

    plugins = []

    # Using any iterable to create a snapshot of sys.modules can occassionally
    # fail in a rare case when modules are imported in parallel by different
    # threads.
    #
    # TL;DR: Do NOT use an iterable on the original sys.modules to generate the
    # list

    for name, module in sys.modules.copy().items():
        # If the module isn't actually loaded (such as failed relative imports
        # in Python 2.7), the module will be None and should not be reported.
        if module is None:
            continue

        if name.startswith('newrelic.hooks.'):
            plugins.append(name)

        elif name.find('.') == -1 and hasattr(module, '__file__'):
            # XXX This is disabled as it can cause notable overhead in
            # pathalogical cases. Will be replaced with a new system
            # where have a whitelist of packages we really want version
            # information for and will work out on case by case basis
            # how to extract that from the modules themselves.

            # try:
            #     if 'pkg_resources' in sys.modules:
            #         version = pkg_resources.get_distribution(name).version
            #         if version:
            #             name = '%s (%s)' % (name, version)
            # except Exception:
            #     pass

            plugins.append(name)

    env.append(('Plugin List', plugins))

    return env
