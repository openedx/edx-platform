"""
Internationalization tasks
"""

import re
import subprocess
import sys

from path import Path as path
from paver.easy import cmdopts, needs, sh, task

from .utils.cmd import django_cmd
from .utils.envs import Env
from .utils.timer import timed

try:
    from pygments.console import colorize
except ImportError:
    colorize = lambda color, text: text

DEFAULT_SETTINGS = Env.DEVSTACK_SETTINGS


@task
@needs(
    "pavelib.prereqs.install_prereqs",
    "pavelib.i18n.i18n_validate_gettext",
)
@cmdopts([
    ("verbose", "v", "Sets 'verbose' to True"),
])
@timed
def i18n_extract(options):
    """
    Extract localizable strings from sources
    """
    verbose = getattr(options, "verbose", None)
    cmd = "i18n_tool extract"

    if verbose:
        cmd += " -v"

    sh(cmd)


@task
@timed
def i18n_fastgenerate():
    """
    Compile localizable strings from sources without re-extracting strings first.
    """
    sh("i18n_tool generate")


@task
@needs("pavelib.i18n.i18n_extract")
@timed
def i18n_generate():
    """
    Compile localizable strings from sources, extracting strings first.
    """
    sh("i18n_tool generate")


@task
@needs("pavelib.i18n.i18n_extract")
@timed
def i18n_generate_strict():
    """
    Compile localizable strings from sources, extracting strings first.
    Complains if files are missing.
    """
    sh("i18n_tool generate --strict")


@task
@needs("pavelib.i18n.i18n_extract")
@cmdopts([
    ("settings=", "s", "The settings to use (defaults to devstack)"),
])
@timed
def i18n_dummy(options):
    """
    Simulate international translation by generating dummy strings
    corresponding to source strings.
    """
    settings = options.get('settings', DEFAULT_SETTINGS)

    sh("i18n_tool dummy")
    # Need to then compile the new dummy strings
    sh("i18n_tool generate")

    # Generate static i18n JS files.
    for system in ['lms', 'cms']:
        sh(django_cmd(system, settings, 'compilejsi18n'))


@task
@timed
def i18n_validate_gettext():
    """
    Make sure GNU gettext utilities are available
    """

    returncode = subprocess.call(['which', 'xgettext'])

    if returncode != 0:
        msg = colorize(
            'red',
            "Cannot locate GNU gettext utilities, which are "
            "required by django for internationalization.\n (see "
            "https://docs.djangoproject.com/en/dev/topics/i18n/"
            "translation/#message-files)\nTry downloading them from "
            "http://www.gnu.org/software/gettext/ \n"
        )

        sys.stderr.write(msg)
        sys.exit(1)


@task
@timed
def i18n_validate_transifex_config():
    """
    Make sure config file with username/password exists
    """
    home = path('~').expanduser()
    config = home / '.transifexrc'

    if not config.isfile or config.getsize == 0:
        msg = colorize(
            'red',
            "Cannot connect to Transifex, config file is missing"
            " or empty: {config} \nSee "
            "http://help.transifex.com/features/client/#transifexrc \n".format(
                config=config,
            )
        )

        sys.stderr.write(msg)
        sys.exit(1)


@task
@needs("pavelib.i18n.i18n_validate_transifex_config")
@timed
def i18n_transifex_push():
    """
    Push source strings to Transifex for translation
    """
    sh("i18n_tool transifex push")


@task
@needs("pavelib.i18n.i18n_validate_transifex_config")
@timed
def i18n_transifex_pull():
    """
    Pull translated strings from Transifex
    """
    sh("i18n_tool transifex pull")


@task
@timed
def i18n_rtl():
    """
    Pull all RTL translations (reviewed AND unreviewed) from Transifex
    """
    sh("i18n_tool transifex rtl")

    print "Now generating langugage files..."

    sh("i18n_tool generate --rtl")

    print "Committing translations..."
    sh('git clean -fdX conf/locale')
    sh('git add conf/locale')
    sh('git commit --amend')


@task
@timed
def i18n_ltr():
    """
    Pull all LTR translations (reviewed AND unreviewed) from Transifex
    """
    sh("i18n_tool transifex ltr")

    print "Now generating langugage files..."

    sh("i18n_tool generate --ltr")

    print "Committing translations..."
    sh('git clean -fdX conf/locale')
    sh('git add conf/locale')
    sh('git commit --amend')


@task
@needs(
    "pavelib.i18n.i18n_clean",
    "pavelib.i18n.i18n_transifex_pull",
    "pavelib.i18n.i18n_extract",
    "pavelib.i18n.i18n_dummy",
    "pavelib.i18n.i18n_generate_strict",
)
@timed
def i18n_robot_pull():
    """
    Pull source strings, generate po and mo files, and validate
    """

    # sh('paver test_i18n')
    # Tests were removed from repo, but there should still be tests covering the translations
    # TODO: Validate the recently pulled translations, and give a bail option
    sh('git clean -fdX conf/locale/rtl')
    sh('git clean -fdX conf/locale/eo')
    print "\n\nValidating translations with `i18n_tool validate`..."
    sh("i18n_tool validate")

    con = raw_input("Continue with committing these translations (y/n)? ")

    if con.lower() == 'y':
        sh('git add conf/locale')
        sh('git add cms/static/js/i18n')
        sh('git add lms/static/js/i18n')

        sh(
            'git commit --message='
            '"Update translations (autogenerated message)" --edit'
        )


@task
@timed
def i18n_clean():
    """
    Clean the i18n directory of artifacts
    """
    sh('git clean -fdX conf/locale')


@task
@needs(
    "pavelib.i18n.i18n_clean",
    "pavelib.i18n.i18n_extract",
    "pavelib.i18n.i18n_transifex_push",
)
@timed
def i18n_robot_push():
    """
    Extract new strings, and push to transifex
    """
    pass


@task
@needs(
    "pavelib.i18n.i18n_validate_transifex_config",
    "pavelib.i18n.i18n_generate",
)
@timed
def i18n_release_push():
    """
    Push release-specific resources to Transifex.
    """
    resources = find_release_resources()
    sh("i18n_tool transifex push " + " ".join(resources))


@task
@needs(
    "pavelib.i18n.i18n_validate_transifex_config",
)
@timed
def i18n_release_pull():
    """
    Pull release-specific translations from Transifex.
    """
    resources = find_release_resources()
    sh("i18n_tool transifex pull " + " ".join(resources))


def find_release_resources():
    """
    Validate the .tx/config file for release files, returning the resource names.

    For working with release files, the .tx/config file should have exactly
    two resources defined named "release-*".  Check that this is true.  If
    there's a problem, print messages about it.

    Returns a list of resource names, or raises ValueError if .tx/config
    doesn't have two resources.

    """
    # An entry in .tx/config for a release will look like this:
    #
    #    [edx-platform.release-dogwood]
    #    file_filter = conf/locale/<lang>/LC_MESSAGES/django.po
    #    source_file = conf/locale/en/LC_MESSAGES/django.po
    #    source_lang = en
    #    type = PO
    #
    #    [edx-platform.release-dogwood-js]
    #    file_filter = conf/locale/<lang>/LC_MESSAGES/djangojs.po
    #    source_file = conf/locale/en/LC_MESSAGES/djangojs.po
    #    source_lang = en
    #    type = PO

    rx_release = r"^\[([\w-]+\.release-[\w-]+)\]$"
    with open(".tx/config") as tx_config:
        resources = re.findall(rx_release, tx_config.read(), re.MULTILINE)

    if len(resources) == 2:
        return resources

    if not resources:
        raise ValueError("You need two release-* resources defined to use this command.")
    else:
        msg = "Strange Transifex config! Found these release-* resources:\n" + "\n".join(resources)
        raise ValueError(msg)


"""
Eliteu Custom Command
"""
import polib
import os
import re

from os import remove, walk
from shutil import move
from tempfile import mkstemp


def find_specific_resource(lang):
    LOCALE_DIR = "conf/locale/{lang}/LC_MESSAGES"
    resource_dir = LOCALE_DIR.format(lang=lang)
    flist = os.listdir(resource_dir)

    result = filter(lambda x: os.path.splitext(x)[1] == '.po', flist)
    resource = [os.path.join(resource_dir, i) for i in result]
    return resource


def extract_invalid(fpath):
    filename = os.path.basename(fpath)
    dirname = os.path.dirname(fpath)
    name = os.path.join(dirname, 'invalid-' + filename)
    zhPattern = re.compile(u'[\u4e00-\u9fa5]+')

    # create if not exists, truncate if exists.
    if not os.path.exists(name):
        f = open(name, 'w')
        f.close()
    else:
        f = open(name, 'w')
        f.seek(0)
        f.truncate()
        f.close()
        
    source = polib.pofile(fpath)
    target = polib.pofile(name)
    target.header = source.header
    target.metadata = source.metadata

    for msg in source:
        if zhPattern.search(msg.msgid) is not None:
            target.append(msg)

    if len(target) > 0:
        target.sort(key=lambda x: len(x.msgid), reverse=True)
        target.save()
    else:
        os.remove(name)


def code_replace(source):
    BASE_DIR = "/edx/app/edxapp/edx-platform"
    pomsgs = polib.pofile(source)

    for msg in pomsgs:
        # A list of file path
        occurrences = msg.occurrences
        for (path, line) in occurrences:
            fpath = os.path.join(BASE_DIR, path)
            if os.path.exists(fpath) and msg.msgstr != '':
                msgid = msg.msgid.encode('utf-8')
                msgstr = msg.msgstr.encode('utf-8')
                replace(fpath, msgid, msgstr)


def replace(source_file_path, pattern, substring):
    
    def need_to_pass(line):
        # comment need to pass
        c1 = line.lstrip().startswith('#')
        c2 = line.lstrip().startswith("//")
        c3 = line.lstrip().startswith('<! --')
        result = c1 or c2 or c3
        return result

    fh, target_file_path = mkstemp()
    target_file = open(target_file_path, 'w')
    source_file = open(source_file_path, 'r')

    for line in source_file:
        if pattern in line and not need_to_pass(line):
            target_file.write(line.replace(pattern, substring))
        else:
            target_file.write(line)

    target_file.close()
    source_file.close()
    remove(source_file_path)
    move(target_file_path, source_file_path)


def change_position(fpath):
    source = polib.pofile(fpath)

    fh, target_file_path = mkstemp()
    target = open(target_file_path, 'w')
    target.close()
    target = polib.pofile(target_file_path)
    zhPattern = re.compile(u'[\u4e00-\u9fa5]+')

    target.header = source.header
    target.metadata = source.metadata

    for s in source:
        valid = zhPattern.search(s.msgid)
        if valid is not None:
            if s.msgstr != "":
                s.msgid, s.msgstr = s.msgstr, s.msgid
        target.append(s)

    target.save()
    remove(fpath)
    move(target_file_path, fpath)  


@task
def i18n_third_party():
    sh("/bin/cp -rf ../edx-membership/conf/locale/en/LC_MESSAGES/django.po conf/locale/en/LC_MESSAGES/membership.po")
    sh("/bin/cp -rf ../edx-membership/conf/locale/en/LC_MESSAGES/djangojs.po conf/locale/en/LC_MESSAGES/membership-js.po")
    

@task
@needs(
    "pavelib.i18n.i18n_clean",
)
@timed
def i18n_update():
    # Step1: extract new word
    # Step2: push to transifex and validate
    # Step3: generate
    sh("i18n_tool extract")
    sh("paver i18n_third_party")
    sh("i18n_tool transifex push")
    sh("i18n_tool validate")


@task
@needs(
    "pavelib.i18n.i18n_transifex_pull",
)
@timed
def i18n_replace():
    # Step1: pull transifex file
    # Step2: extract invalid word
    # Step3: replace code
    # Step4: remove invalid file
    # Step5: change position of code
    files = find_specific_resource('zh_CN')
    remove = filter(lambda x: x.split('/')[-1].startswith('invalid'), files)
    map(os.remove, remove)
    
    resource = find_specific_resource('zh_CN')
    map(extract_invalid, resource)

    flist = find_specific_resource('zh_CN')
    invalid = filter(lambda x: x.split('/')[-1].startswith('invalid'), flist)
    map(code_replace, invalid)
    
    map(os.remove, invalid)
    map(change_position, resource)

   
@task
@timed
def i18n_push():
    # Re extract after code replace
    sh("i18n_tool extract")
    sh("paver i18n_third_party")
    sh("i18n_tool validate")
    sh("i18n_tool generate --strict")
    sh("python manage.py cms compilejsi18n")
    sh("python manage.py lms compilejsi18n")

    msg = colorize(
            'green',
            "Please checking your code after update and replace."
        )
    print msg

    con = raw_input("Are you want to replace all sources in transifex (y/n)? ")
    if con.lower() == 'y':
        sh("tx push -s -t -l zh_CN")
