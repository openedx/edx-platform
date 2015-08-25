"""
Hotshot/CProfile Profiler Middleware

- Original version taken from http://www.djangosnippets.org/snippets/186/
- Original author: udfalkso
- Modified by: Shwagroo Team, Gun.io, and many others
- This version implemented by the Solutions Team @ edX.org
- Various bits derived from Internet references, primarily:
   * https://code.djangoproject.com/wiki/ProfilingDjango
   * https://gun.io/blog/fast-as-fuck-django-part-1-using-a-profiler/
   * https://blog.safaribooksonline.com/2013/11/21/profiling-django-via-middleware/
   * http://www.jeffknupp.com/blog/2012/02/14/profiling-django-applications-a-journey-from-1300-to-2-queries/
- The profiler is enabled via feature flag in settings.py -- see devstack.py and test.py
- Once enabled, simply add "prof=1" to the query string to profile your view
- Include "&profile_mode=help" for more information (see generate_help below)

"""

import hotshot
import hotshot.stats
import os
import pstats
import re
import shutil
import subprocess
import sys
import tempfile
import time
import threading

from django.conf import settings
from django.core.exceptions import MiddlewareNotUsed

try:
    import cProfile
    HAS_CPROFILE = True
except ImportError:
    HAS_CPROFILE = False

try:
    import cStringIO as StringIO
except ImportError:
    import StringIO

THREAD_LOCAL = threading.local()


def which(program):
    """
    Helper method to return the path of the named program in the PATH,
    or None if no such executable program can be found.
    """
    def is_exe(fpath):
        """
        Internal helper to confirm that this is an executable program
        """
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, _fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file
    return None


class BaseProfilerMiddleware(object):
    """
    This class performs the actual work of profiling and generating the
    report output.  The child classes defined below address some
    implementation-specific idiosyncrasies for each profiler.
    """
    def process_request(self, request):
        """
        Set up the profiler for use
        """
        print 'process_request'
        # Capture some values/references to use across the operations
        THREAD_LOCAL.profiler_requested = request.GET.get('prof', False)

        # Ensure we're allowed to use the profiler
        if THREAD_LOCAL.profiler_requested and not settings.DEBUG and not request.user.is_superuser:
            raise MiddlewareNotUsed()

        # Ensure the profiler being requested is actually installed/available
        if not hasattr(THREAD_LOCAL, 'profiler_type') or THREAD_LOCAL.profiler_type is None:
            THREAD_LOCAL.profiler_type = request.GET.get('profiler_type', 'hotshot')
        if self.profiler_type() == THREAD_LOCAL.profiler_type:
            if not self.profiler_installed():
                return MiddlewareNotUsed()

        # Create the container we'll be using to store the raw profiler data
        THREAD_LOCAL.data_file = tempfile.NamedTemporaryFile()

    def process_view(self, request, callback, callback_args, callback_kwargs):
        """
        Enable the profiler and begin collecting data about the view
        Note that this misses the rest of Django's request processing (other middleware, etc.)
        """
        # Ensure the profiler being requested is actually installed/available
        if THREAD_LOCAL.profiler_type is None:
            THREAD_LOCAL.profiler_type = request.GET.get('profiler_type', 'hotshot')
        if self.profiler_type() == THREAD_LOCAL.profiler_type:
            if not self.profiler_installed():
                return MiddlewareNotUsed()

            THREAD_LOCAL.profiler = self.profiler_start()
            return THREAD_LOCAL.profiler.runcall(callback, request, *callback_args, **callback_kwargs)

    def _generate_console_response(self, stats_str, stats_summary):
        """
        Output directly to the console -- helpful during unit testing or
        for viewing code executions in devstack
        """
        print stats_str
        print stats_summary

    def _generate_text_response(self, stats_str, stats_summary, response):
        """
        Output the call stats to the browser as plain text
        """
        response['Content-Type'] = 'text/plain'
        response.content = stats_str
        response.content = "\n".join(response.content.split("\n")[:40])
        response.content += "\n\n"
        response.content += stats_summary

    def _generate_html_response(self, stats_str, stats_summary, response):
        """
        Output the call stats to the browser wrapped in HTML tags
        Feel free to improve the HTML structure!!!
        """
        response['Content-Type'] = 'text/html'
        response.content = '<pre>{}{}</pre>'.format(stats_str, stats_summary)

    def _generate_pdf_response(self, response):
        """
        Output a pretty picture of the call tree (boxes and arrows)
        """
        if not which('dot'):
            raise Exception('Could not find "dot" from Graphviz; please install Graphviz to enable call graph generation')
        if not which('gprof2dot'):
            raise Exception('Could not find gprof2dot; have you updated your dependencies recently?')
        command = ('gprof2dot -f pstats {} | dot -Tpdf'.format(THREAD_LOCAL.data_file.name))
        process = subprocess.Popen(
            command,
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE)
        output = process.communicate()[0]
        return_code = process.poll()
        if return_code:
            raise Exception('gprof2dot/dot exited with {}'.format(return_code))
        response['Content-Type'] = 'application/pdf'
        response.content = output

    def _generate_svg_response(self, response):
        """
        Output a pretty picture of the call tree (boxes and arrows)
        """
        # Set up the data file
        profile_name = '{}_{}'.format(self.profiler_type(), time.time())
        profile_data = '/tmp/{}.dat'.format(profile_name)
        shutil.copy(THREAD_LOCAL.data_file.name, profile_data)
        os.chmod(profile_data, 0666)
        # Create the output file
        profile_svg = '/tmp/{}.svg'.format(profile_name)
        old = os.path.abspath('.')
        os.chdir('/tmp')
        command = 'gprof2dot -f pstats {} | dot -Tsvg -o {}'.format(profile_data, profile_svg)
        try:
            output = subprocess.call(command, shell=True)
        except Exception:  # pylint: disable=W0703
            output = 'Error during call to gprof2dot/dot'
        os.chdir(old)
        if os.path.exists(profile_svg):
            response['Content-Type'] = 'image/svg+xml'
            f = open(profile_svg)
            response.content = f.read()
            f.close()
        else:
            response['Content-Type'] = 'text/plain'
            response.content = output

    def _generate_raw_response(self, response):
        """
        Output the raw stats data to the browser -- the caller can then
        save the information to a local file and do something else with it
        Could be used as an integration point in the future for real-time
        diagrams, charts, reports, etc.
        """
        # Set up the data faile (this is all we do in this particular case)
        profile_name = '{}_{}'.format(self.profiler_type(), time.time())
        profile_data = '/tmp/{}.dat'.format(profile_name)
        shutil.copy(THREAD_LOCAL.data_file.name, profile_data)
        os.chmod(profile_data, 0666)
        # Return the raw data directly to the caller/browser (useful for API scenarios)
        f = open(profile_data)
        response.content = f.read()
        f.close()

    def process_response(self, request, response):
        """
        Most of the heavy lifting takes place in this base process_response operation
        It seems process_response can be invoked without a prior invocation
        of process request and/or process view, so we need to put in a guard
        """
        if not hasattr(THREAD_LOCAL, 'profiler_type') or THREAD_LOCAL.profiler_type is None:
            THREAD_LOCAL.profiler_type = request.GET.get('profiler_type', 'hotshot')
        if self.profiler_type() == THREAD_LOCAL.profiler_type and THREAD_LOCAL.profiler is not None:
            if not self.profiler_installed():
                return MiddlewareNotUsed()

            # The caller may want to view the runtime help documentation
            profiler_mode = request.GET.get('profiler_mode', 'normal')
            if profiler_mode == 'help':
                response['Content-Type'] = 'text/plain'
                response.content = self.generate_help()
                return response

            # Set up a redirected stdout location (hides output from console)
            old_stdout = sys.stdout
            temp_stdout = StringIO.StringIO()
            sys.stdout = temp_stdout

            # Load the statistics collected by the profiler
            stats = self.profiler_stop(temp_stdout)

            # Sort the statistics according to the caller's wishes
            # See # http://docs.python.org/2/library/profile.html#pstats.Stats.sort_stats
            # for the all of the fields you can sort on (some in generate_help below)
            profiler_sort = request.GET.get('profiler_sort', 'time')
            if profiler_sort == 'time':
                profiler_sort = 'time,calls'
            stats.sort_stats(*profiler_sort.split(','))

            # Strip out the directories from the report, if so desired
            strip_dirs = request.GET.get('profiler_strip', False)
            if strip_dirs:
                stats.strip_dirs()

            # Pare down the statistics data further, if specified
            restrictions = []
            # Regex filter
            if request.GET.get('profile_filter'):
                restrictions.append(request.GET['profile_filter'])
            # Cut the list down to either a fraction of the set or a specific line count
            if request.GET.get('profile_fraction'):
                restrictions.append(float(request.GET['profile_fraction']))
            elif request.GET.get('profile_lines'):
                restrictions.append(int(request.GET['profile_lines']))
            # If no size restriction and we're not filtering, trim stats to a reasonable amount
            elif not request.GET.get('filter'):
                restrictions.append(.1)

            # Send the statistics data to the redirected stdout location,
            # then put stdout back to its original configuration
            stats.print_stats(*restrictions)
            stats_str = temp_stdout.getvalue()
            sys.stdout.close()
            sys.stdout = old_stdout

            # Format the response
            if response and response.content and stats_str:
                stats_summary = self.summary_for_files(stats_str)
                response_format = request.GET.get('profiler_format', 'console')
                # Console format sends the profiler result to stdout, preserving current response content
                # All other formats replace response content with the profiler result
                if response_format == 'console':
                    self._generate_console_response(stats_str, stats_summary)
                elif response_format == 'text':
                    self._generate_text_response(stats_str, stats_summary, response)
                elif response_format == 'html':
                    self._generate_html_response(stats_str, stats_summary, response)
                elif response_format == 'pdf':
                    self._generate_pdf_response(response)
                elif response_format == 'svg':
                    self._generate_svg_response(response)
                elif response_format == 'raw':
                    self._generate_raw_response(response)

        # Clean up the stuff we stuffed into thread_local and then return the response to the caller
        THREAD_LOCAL.profiler_type = None
        THREAD_LOCAL.profiler_requested = None
        return response

    def profiler_type(self):
        """
        Parent method -- should be overridden by child
        """
        return 'undefined'

    def profiler_installed(self):
        """
        Parent method -- should be overridden by child
        """
        return False

    def profiler_start(self):
        """
        Parent method -- should be overridden by child
        """
        return MiddlewareNotUsed()

    def profiler_stop(self, stream):  # pylint: disable=W0613
        """
        Parent method -- should be overridden by child
        """
        return MiddlewareNotUsed()

    def get_group(self, file_name):
        """
        Finds a matching group for a given line (statistic) in the file
        """
        group_prefix_re = [
            re.compile("^.*/django/[^/]+"),
            re.compile("^(.*)/[^/]+$"),  # extract module path
            re.compile(".*"),           # catch strange entries
        ]
        for prefix in group_prefix_re:
            name = prefix.findall(file_name)
            if name:
                return name[0]

    def get_summary(self, results_dict, total):
        """
        Does the actual rolling up of stats info into a group
        """
        results = [(item[1], item[0]) for item in results_dict.items()]
        results.sort(reverse=True)
        result = results[:40]
        res = "      tottime\n"
        for item in result:
            res += "%4.1f%% %7.3f %s\n" % (100 * item[0] / total if total else 0, item[0], item[1])
        return res

    def summary_for_files(self, stats_str):
        """
        Rolls up the statistics generated by the profiler into some
        useful aggregates (by file and by group)
        """
        stats_str = stats_str.split("\n")[5:]
        mystats = {}
        mygroups = {}
        total = 0
        iteration = 0
        for stat in stats_str:
            iteration = iteration + 1
            if iteration > 2:
                words_re = re.compile(r'\s+')
                fields = words_re.split(stat)
                if len(fields) == 7:
                    stat_time = float(fields[2])
                    total += stat_time
                    file_name = fields[6].split(":")[0]
                    if file_name not in mystats:
                        mystats[file_name] = 0
                    mystats[file_name] += stat_time
                    group = self.get_group(file_name)
                    if group not in mygroups:
                        mygroups[group] = 0
                    mygroups[group] += stat_time
        summary_string = " ---- By file ----\n\n" + self.get_summary(mystats, total) + "\n" + \
                         " ---- By group ---\n\n" + self.get_summary(mygroups, total)
        return summary_string

    def generate_help(self):
        """
        Provide some useful operational info to the caller
        """
        return "########## PROFILER HELP ##########\n\n\n" + \
            "Profiler Options (query string params):\n\n" + \
            "profiler_type: hotshot (default), cprofile \n" + \
            "profiler_mode: normal (default), help \n" + \
            "profiler_sort: time (default) calls, cumulative, file, module, ncalls \n" + \
            "profiler_format: console (default), text, html, pdf, svg, raw \n\n\n" + \
            "More info: \n\n" + \
            "https://docs.python.org/2/library/hotshot.html \n" + \
            "https://docs.python.org/2/library/profile.html#module-cProfile \n"


class HotshotProfilerMiddleware(BaseProfilerMiddleware):
    """
    Hotshot is a replacement for the existing profile module.
    See https://docs.python.org/2/library/hotshot.html for more info
    WARNING: The Hotshot profiler is not thread safe.
    """
    def __init__(self, *args, **kwargs):
        super(HotshotProfilerMiddleware, self).__init__(*args, **kwargs)

    def profiler_type(self):
        """
        Use this value to select the profiler via query string
        """
        return 'hotshot'

    def profiler_installed(self):
        """
        Hotshot is native and available for use
        """
        return True

    def profiler_start(self):
        """
        Turn on the profiler and begin collecting data
        """
        return hotshot.Profile(THREAD_LOCAL.data_file.name)

    def profiler_stop(self, stream):  # pylint: disable=W0221
        """
        Store profiler data in file and return statistics to caller
        """
        THREAD_LOCAL.profiler.close()
        return hotshot.stats.load(THREAD_LOCAL.data_file.name)


class CProfileProfilerMiddleware(BaseProfilerMiddleware):
    """
    CProfile is a runtime profiler available natively in Python
    See https://docs.python.org/2/library/profile.html#module-cProfile for more info
    """
    def __init__(self):
        super(CProfileProfilerMiddleware, self).__init__()

    def profiler_type(self):
        """
        Use this value to select the profiler via query string
        """
        return 'cprofile'

    def profiler_installed(self):
        """
        Apparently CProfile is not native, and many examples simply
        failover to the regular 'profile' module.  Maybe we should, too
        """
        return HAS_CPROFILE

    def profiler_start(self):
        """
        Turn on the profiler and begin collecting data
        """
        return cProfile.Profile()

    def profiler_stop(self, stream):
        """
        Store profiler data in file and return statistics to caller
        """
        THREAD_LOCAL.profiler.create_stats()
        THREAD_LOCAL.profiler.dump_stats(THREAD_LOCAL.data_file.name)
        return pstats.Stats(THREAD_LOCAL.profiler, stream=stream)
