"""
Internationalization tasks
"""

import os
import polib
import re
import subprocess
import sys

from shutil import move
from tempfile import mkstemp
from os import remove, walk
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


""" Eliteu command """
@task
def i18n_third_party():
    sh("cp ../edx-membership/conf/locale/en/LC_MESSAGES/django.po conf/locale/en/LC_MESSAGES/membership-saved.po")
    sh("cp ../edx-membership/conf/locale/en/LC_MESSAGES/djangojs.po conf/locale/en/LC_MESSAGES/membershipjs-saved.po")
    sh("mv conf/locale/en/LC_MESSAGES/membership-saved.po conf/locale/en/LC_MESSAGES/membership.po")
    sh("mv conf/locale/en/LC_MESSAGES/membershipjs-saved.po conf/locale/en/LC_MESSAGES/membership-js.po")    


@task
def i18n_check():
    base_dir = 'conf/locale/zh_CN/LC_MESSAGES'
    names = ['django.po', 'djangojs.po']
    zhPattern = re.compile(u'[\u4e00-\u9fa5]+')

    for name in names:
        spath = os.path.join(base_dir, name)
        tpath = os.path.join(base_dir, 'zh-' + name)
        source = polib.pofile(spath)

        # create file
        f = open(tpath, 'w')
        f.close()
        target = polib.pofile(tpath)

        for msg in source:
            text = msg.msgid.strip()
            match = zhPattern.search(text)
            if match:
                target.append(msg)

        target.sort(key=lambda x: len(x.msgid), reverse=True)
        target.save()


@task
@needs(
    "pavelib.i18n.i18n_check",
)
@timed
def i18n_replace():
    BASE_DIR = '/edx/app/edxapp/edx-platform/'
    base_dir = 'conf/locale/zh_CN/LC_MESSAGES'
    names = ['zh-django.po', 'zh-djangojs.po']
    source = [os.path.join(base_dir, name) for name in names]

    for s in source:
        pomsgs = polib.pofile(s)

        for msg in pomsgs:
            msgid = msg.msgid.encode('utf-8')
            msgstr = msg.msgstr.encode('utf-8')

            # A list of file path
            occurrences = msg.occurrences

            for (path, line) in occurrences:
                fpath = os.path.join(BASE_DIR, path)

                if os.path.exists(fpath) and os.path.isfile(fpath):
                    if msgstr != '':
                        replace(fpath, msgid, msgstr)


@task
def i18n_exchange():
    base_dir = 'conf/locale/zh_CN/LC_MESSAGES'
    names = ['django.po', 'djangojs.po']
    source = [os.path.join(base_dir, name) for name in names]

    for s in source:
        exchange(s)


@task
@needs(
    "pavelib.i18n.i18n_third_party",
    "pavelib.i18n.i18n_extract",
    "pavelib.i18n.i18n_generate",
    "pavelib.i18n.i18n_transifex_pull",
    "pavelib.i18n.i18n_transifex_push",
    "pavelib.i18n.i18n_dummy",
    "pavelib.i18n.i18n_generate_strict",
    "pavelib.i18n.i18n_replace",
    "pavelib.i18n.i18n_exchange",
)
@timed
def i18n_eliteu_update():
    """
    Pull source strings, generate po and mo files, and validate
    """

    # sh('paver test_i18n')
    # Tests were removed from repo, but there should still be tests covering the translations
    # TODO: Validate the recently pulled translations, and give a bail option
    sh('git clean -fdX conf/locale/rtl')
    sh('git clean -fdX conf/locale/eo')
    print "\n\nValidating translations with `i18n_tool validate`..."

    sh("rm conf/locale/zh_CN/LC_MESSAGES/zh-django.po")
    sh("rm conf/locale/zh_CN/LC_MESSAGES/zh-djangojs.po")
    sh("rm conf/locale/zh_HANS/LC_MESSAGES/zh-django.po")
    sh("rm conf/locale/zh_HANS/LC_MESSAGES/zh-djangojs.po")
    sh("rm conf/locale/zh_HANS/LC_MESSAGES/*.mo")
    sh("rm conf/locale/zh_HANS/LC_MESSAGES/*.mo")
    sh("i18n_tool validate")

    con = raw_input("Continue with committing these translations (y/n)? ")

    if con.lower() == 'y':
        sh('git add conf/locale/zh_CN')
        sh('git add conf/locale/zh_HANS')
        sh('git add cms/static/js/i18n')
        sh('git add lms/static/js/i18n')

    dirty = i18n_dirty_check()
    if dirty:
        print "\n\nStill has invalid word in po file."
    

@task
def i18n_dirty_check():
    base_dir = 'conf/locale/en/LC_MESSAGES'
    names = ['django.po', 'djangojs.po']
    zhPattern = re.compile(u'[\u4e00-\u9fa5]+')
    flag = False

    for name in names:
        spath = os.path.join(base_dir, name)
        source = polib.pofile(spath)

        for msg in source:
            text = msg.msgid.strip()
            match = zhPattern.search(text)
            if match:
                flag = True
                break
    
    if flag:
        print "\nDirty."
    else:
        print "\nPure."

    return flag


def replace(source_file_path, pattern, substring):
    """
    Update msgid with specified pattern and replace to substring

    :param source_file_path:
    :param pattern:
    :param substring:
    :return:
    """

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


def exchange(source_file_path):
    """
    Exchange msgid and msgstr position of zh.po

    :param source_file_path: File which need to be exchange
    :return:
    """

    source = polib.pofile(source_file_path)

    fh, target_file_path = mkstemp()
    target = open(target_file_path, 'w')
    target.close()
    target = polib.pofile(target_file_path)
    zhPattern = re.compile(u'[\u4e00-\u9fa5]+')

    for s in source:
        match = zhPattern.search(s.msgid.strip())
        if match:
            s.msgid, s.msgstr = s.msgstr, s.msgid
        target.append(s)

    target.save()
    remove(source_file_path)
    move(target_file_path, source_file_path)

