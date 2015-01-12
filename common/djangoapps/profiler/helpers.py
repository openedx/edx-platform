"""
Helper methods for the profiler middleware
"""
import os
import re
import shutil
import subprocess
from textwrap import dedent
import time


def generate_help():
    """
    Provide some useful operational info to the caller
    """
    help = dedent("""\
        ########## PROFILER HELP ##########


        Profiler Options (query string params):

        profiler_type: hotshot (default), cprofile
        profiler_mode: normal (default), help
        profiler_sort: time (default) calls, cumulative, file, module, ncalls
        profiler_format: console (default), text, html, pdf, svg, raw


        More info:

        https://docs.python.org/2/library/hotshot.html
        https://docs.python.org/2/library/profile.html#module-cProfile
    """)
    return help


def generate_console_response(stats_str, stats_summary):
    """
    Output directly to the console -- helpful during unit testing or
    for viewing code executions in devstack
    """
    print stats_str
    print stats_summary


def generate_text_response(stats_str, stats_summary, response):
    """
    Output the call stats to the browser as plain text
    """
    response['Content-Type'] = 'text/plain'
    response.content = stats_str
    response.content = "\n".join(response.content.split("\n")[:40])
    response.content += "\n\n"
    response.content += stats_summary


def generate_html_response(stats_str, stats_summary, response):
    """
    Output the call stats to the browser wrapped in HTML tags
    Feel free to improve the HTML structure!!!
    """
    response['Content-Type'] = 'text/html'
    response.content = '<pre>{}{}</pre>'.format(stats_str, stats_summary)


def generate_pdf_response(filename, response):
    """
    Output a pretty picture of the call tree (boxes and arrows)
    """
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

    if not which('dot'):
        raise Exception('Could not find "dot" from Graphviz; please install Graphviz to enable call graph generation')
    if not which('gprof2dot'):
        raise Exception('Could not find gprof2dot; have you updated your dependencies recently?')
    command = ('gprof2dot -f pstats {} | dot -Tpdf'.format(filename))
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


def generate_svg_response(filename, profiler_type, response):
    """
    Output a pretty picture of the call tree (boxes and arrows)
    """
    # Set up the data file
    profile_name = '{}_{}'.format(profiler_type, time.time())
    profile_data = '/tmp/{}.dat'.format(profile_name)
    shutil.copy(filename, profile_data)
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


def generate_raw_response(profiler_type, filename, response):
    """
    Output the raw stats data to the browser -- the caller can then
    save the information to a local file and do something else with it
    Could be used as an integration point in the future for real-time
    diagrams, charts, reports, etc.
    """
    # Set up the data faile (this is all we do in this particular case)
    profile_name = '{}_{}'.format(profiler_type, time.time())
    profile_data = '/tmp/{}.dat'.format(profile_name)
    shutil.copy(filename, profile_data)
    os.chmod(profile_data, 0666)
    # Return the raw data directly to the caller/browser (useful for API scenarios)
    f = open(profile_data)
    response.content = f.read()
    f.close()


def _get_group(file_name):
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


def _get_summary(results_dict, total):
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


def summary_for_files(stats_str):
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
                if not file_name in mystats:
                    mystats[file_name] = 0
                mystats[file_name] += stat_time
                group = _get_group(file_name)
                if not group in mygroups:
                    mygroups[group] = 0
                mygroups[group] += stat_time
    summary_string = " ---- By file ----\n\n" + _get_summary(mystats, total) + "\n" + \
                     " ---- By group ---\n\n" + _get_summary(mygroups, total)
    return summary_string
