import os
import glob
import re
import shutil
import sys
import six
import nbgrader.apps

from textwrap import dedent
from clear_docs import run, clear_notebooks


def autogen_command_line(root):
    """Generate command line documentation."""

    header = dedent(
        """
        {}
        {}

        ::

        """
    )

    apps = [
        'AssignApp',
        'AutogradeApp',
        'CollectApp',
        'DbAssignmentAddApp',
        'DbAssignmentImportApp',
        'DbAssignmentListApp',
        'DbAssignmentRemoveApp',
        'DbStudentAddApp',
        'DbStudentImportApp',
        'DbStudentListApp',
        'DbStudentRemoveApp',
        'ExportApp',
        'FeedbackApp',
        'FetchApp',
        'ListApp',
        'NbGraderApp',
        'QuickStartApp',
        'ReleaseApp',
        'SubmitApp',
        'UpdateApp',
        'ValidateApp',
        'ZipCollectApp',
    ]

    print('Generating command line documentation')
    orig_stdout = sys.stdout

    for app in apps:
        cls = getattr(nbgrader.apps, app)
        buf = sys.stdout = six.StringIO()
        cls().print_help(True)
        buf.flush()
        helpstr = buf.getvalue()
        helpstr = "\n".join(["    " + x for x in helpstr.split("\n")])

        name = cls.name.replace(" ", "-")
        destination = os.path.join(root, 'command_line_tools/{}.rst'.format(name))
        with open(destination, 'w') as f:
            f.write(header.format(cls.name.replace("-", " "), "=" * len(cls.name)))
            f.write(helpstr)

    sys.stdout = orig_stdout


def autogen_config(root):
    """Generate an example configuration file"""

    header = dedent(
        """
        Configuration options
        =====================

        These options can be set in ``nbgrader_config.py``, or at the command
        line when you start it.

        Note: the ``nbgrader_config.py`` file can be either located in the same
        directory as where you are running the nbgrader commands (which is most
        likely the root of your course directory), or you can place it in one of
        a number of locations on your system. These locations correspond to the
        configuration directories that Jupyter itself looks in; you can find out
        what these are by running ``jupyter --paths``.

        """
    )

    print('Generating example configuration file')
    config = nbgrader.apps.NbGraderApp().document_config_options()
    destination = os.path.join(root, 'configuration', 'config_options.rst')
    with open(destination, 'w') as f:
        f.write(header)
        f.write(config)


def execute_notebooks(root):
    """Execute notebooks"""
    print("Executing notebooks in '{}'...".format(os.path.abspath(root)))

    cwd = os.getcwd()
    os.chdir(root)

    # hack to convert links to ipynb files to html
    for filename in sorted(glob.glob('user_guide/*.ipynb')):
        run([
            sys.executable, '-m', 'jupyter', 'nbconvert',
            '--inplace',
            '--execute',
            '--FilesWriter.build_directory=user_guide',
            filename
        ])

    os.chdir(cwd)


def convert_notebooks(root):
    """Convert notebooks to rst and html"""
    print("Converting notebooks in '{}'...".format(os.path.abspath(root)))

    cwd = os.getcwd()
    os.chdir(root)

    # hack to convert links to ipynb files to html
    for filename in sorted(glob.glob('user_guide/*.ipynb')):
        run([
            sys.executable, '-m', 'jupyter', 'nbconvert',
            '--to', 'rst',
            '--FilesWriter.build_directory=user_guide',
            filename
        ])

        filename = os.path.splitext(filename)[0] + '.rst'
        with open(filename, 'r') as fh:
            source = fh.read()
        source = re.sub(r"<([^><]*)\.ipynb>", r"<\1.html>", source)
        with open(filename, 'w') as fh:
            fh.write(source)

    # convert examples to html
    for dirname, dirnames, filenames in os.walk('user_guide'):
        if dirname == 'user_guide':
            continue
        if dirname == 'user_guide/images':
            continue
        if os.path.split(dirname)[1] == ".ipynb_checkpoints":
            continue

        build_directory = os.path.join('extra_files', dirname)
        if not os.path.exists(build_directory):
            os.makedirs(build_directory)

        for filename in sorted(filenames):
            if filename.endswith('.ipynb'):
                run([
                    sys.executable, '-m', 'jupyter', 'nbconvert',
                    '--to', 'html',
                    "--FilesWriter.build_directory='{}'".format(build_directory),
                    os.path.join(dirname, filename)
                ])

            else:
                src = os.path.join(dirname, filename)
                dest = os.path.join(build_directory, filename)
                if os.path.exists(dest):
                    os.remove(dest)
                shutil.copy(src, dest)

    os.chdir(cwd)


if __name__ == "__main__":
    root = os.path.abspath(os.path.dirname(__file__))
    clear_notebooks(root)
    execute_notebooks(root)
