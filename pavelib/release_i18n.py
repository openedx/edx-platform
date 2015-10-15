"""
Internationalization tasks for Open edX releases
"""
import sys
from path import Path
from paver.easy import task, cmdopts, needs, sh

# Set this to the name of the current release
# If you change this, be sure to reflect the change in the
# .tx/RELEASE_CONFIGFILE as well.
RELEASE_NAME = 'cypress-release'

# **** Stuff to configure Transifex's configuration file ****
# Name of the Transifex release configuration file (must be present in .tx/ directory)
RELEASE_CONFIGFILE = 'release_config'

# **** Stuff to configure i18n_tool's yaml configuration file ****
BASE_DIR = Path('.').abspath()
# LOCALE_DIR contains the locale files.
# Typically this should be 'edx-platform/conf/locale'
LOCALE_DIR = BASE_DIR.joinpath('conf', 'locale')
# Make sure that we read from conf/locale/release_config.yaml,
# so all calls should include `-c LOCALE_DIR.joinpath('release_config.yaml').normpath()`
CONFIG_LOCATION = LOCALE_DIR.joinpath('release_config.yaml').normpath()

@task
@needs(
    "pavelib.prereqs.install_prereqs",
    "pavelib.i18n.i18n_validate_gettext",
    "pavelib.assets.compile_coffeescript",
)
@cmdopts([
    ("verbose", "v", "Sets 'verbose' to True"),
])
def release_i18n_extract(options):
    """
    Extract localizable strings from sources
    """
    verbose = getattr(options, "verbose", None)
    cmd = "i18n_tool extract -c {config}".format(config=CONFIG_LOCATION)

    if verbose:
        cmd += " -vv"

    sh(cmd)

@task
@needs("pavelib.release_i18n.release_i18n_extract")
def release_i18n_generate_strict():
    """
    Compile localizable strings from sources, extracting strings first.
    Complains if files are missing.
    """
    cmd = "i18n_tool generate -c {config}".format(config=CONFIG_LOCATION)
    sh(cmd + " --strict")


@task
@needs("pavelib.release_i18n.release_i18n_extract")
def release_i18n_dummy():
    """
    Simulate international translation by generating dummy strings
    corresponding to source strings.
    """
    cmd = "i18n_tool dummy -c {config}".format(config=CONFIG_LOCATION)
    sh(cmd)
    # Need to then compile the new dummy strings
    cmd = "i18n_tool generate -c {config}".format(config=CONFIG_LOCATION)
    sh(cmd)


def swap_configuration_files():
    """
    We need to override the default .tx/config file.
    The utility provides no way to do this, so temporarily swap in the
    RELEASE_CONFIGFILE for the .tx/config file.

    Be sure to execute cleanup_configfiles() after running this function.
    """
    # Figure out what directory we're running this command from, and get
    # into the proper place.
    cwd = Path.getcwd()
    try:
        Path.cd(cwd.joinpath('.tx'))
    except OSError:
            msg = (
                "This utility must be run from the edx-platform directory. "
                "Please change to this directory before executing this command."
            )
            raise IOError(msg)
    # Move config to config.swp
    # Move RELEASE_CONFIGFILE to config
    cwd = Path.getcwd()
    for filename in ['config', RELEASE_CONFIGFILE]:
        if cwd.joinpath(filename) not in cwd.files():
            msg = (
                "ERROR: Did not find file named {0} in {1} directory."
            ).format(filename, cwd, cwd.files())
            raise IOError(msg)
    Path.move(cwd.joinpath('config'), cwd.joinpath('config.swp'))
    Path.move(cwd.joinpath(RELEASE_CONFIGFILE), cwd.joinpath('config'))


def cleanup_configfiles():
    """
    Cleans up the mess made by swap_configuration_files
    """
    # Move config to RELEASE_CONFIGFILE
    # Move config.swp to config
    cwd = Path.getcwd()
    if cwd.name != '.tx':
        Path.cd(cwd.joinpath('.tx'))
        cwd = Path.getcwd()
    # If swaps didn't finish all the way, these may not work; try anyway.
    try:
        Path.move(cwd.joinpath('config'), cwd.joinpath(RELEASE_CONFIGFILE))
    except Exception:  # pylint: disable=broad-except
        pass
    try:
        Path.move(cwd.joinpath('config.swp'), cwd.joinpath('config'))
    except Exception:  # pylint: disable=broad-except
        pass


@task
@needs("pavelib.i18n.i18n_validate_transifex_config")
def release_i18n_transifex_push():
    """
    Push source strings to Transifex for translation
    """
    # Need to override default platform .tx/config before running this command
    try:
        swap_configuration_files()
        cmd = "i18n_tool transifex -c {config}".format(config=CONFIG_LOCATION)
        sh("{cmd} push".format(cmd=cmd))
    finally:
        cleanup_configfiles()

@task
@needs(
    "pavelib.release_i18n.release_i18n_extract",
    "pavelib.i18n.i18n_validate_transifex_config"
)
def release_i18n_transifex_push_new():
    """
    Push source strings to Transifex for translation
    """
    # Need to override default platform .tx/config before running this command

    ## TODO: When cutting Dogwood, need to add in some logic to first pull_all
    ## existing translations (even unreviewed), then push all up to the new instance.

    try:
        swap_configuration_files()
        print("\nThis command is intended to push new strings for an Open edX release with name '{}'\nDo NOT run if you're not sure if you're doing the right thing.".format(RELEASE_NAME))
        cmd = "i18n_tool transifex -c {config}".format(config=CONFIG_LOCATION)
        sh("{cmd} push_all".format(cmd=cmd))
    finally:
        # Make sure we straighten up configfiles
        cleanup_configfiles()


@task
@needs("pavelib.i18n.i18n_validate_transifex_config")
def release_i18n_transifex_pull():
    """
    Pull translated strings from Transifex
    """
    # Need to override default platform .tx/config before running this command
    assert_proper_location()
    cmd = "i18n_tool transifex -c {config}".format(config=CONFIG_LOCATION)
    sh("{cmd} pull".format(cmd=cmd))


@task
@needs(
    "pavelib.i18n.i18n_clean",
    "pavelib.release_i18n.release_i18n_transifex_pull",
    "pavelib.release_i18n.release_i18n_extract",
    "pavelib.release_i18n.release_i18n_dummy",
    "pavelib.release_i18n.release_i18n_generate_strict",
)
def release_i18n_robot_pull():
    """
    Pull source strings, generate po and mo files, and validate
    """
    # Validate the recently pulled translations, and give a bail option
    sh('git clean -fdX conf/locale/rtl')
    sh('git clean -fdX conf/locale/eo')
    cmd = "i18n_tool validate -c {config}".format(config=CONFIG_LOCATION)
    print("\n\nValidating translations with `i18n_tool validate`...")
    sh("{cmd}".format(cmd=cmd))

    con = raw_input("Continue with committing these translations (y/n)? ")

    if con.lower() == 'y':
        sh('git add conf/locale')

        sh(
            'git commit --message='
            '"Update translations (autogenerated message)" --edit'
        )


@task
def i18n_clean():
    """
    Clean the i18n directory of artifacts
    """
    sh('git clean -fdX conf/locale')


@task
@needs(
    "pavelib.release_i18n.release_i18n_extract",
    "pavelib.release_i18n.release_i18n_transifex_push",
)
def release_i18n_robot_push():
    """
    Extract new strings, and push to transifex
    """
    pass
