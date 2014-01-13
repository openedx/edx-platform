Paver requires the pre-requisite of psutils

run paver --help for a list of commands

run individual commands using:

paver <command_name>

some commands take parameters


Commands available:

**install_prereqs** (installs ruby, node and python)

Runs following commands:

**install_ruby_prereqs**
**install_node_prereqs**
**install_python_prereqs**


**build_docs** (Invoke sphinx 'make build' to generate docs.)
    "--type=" "Type of docs to compile"
    "--verbose" "Display verbose output"

**show_docs** (Show docs in browser)
    "--type=" "Type of docs to compile"

**doc** (Invoke sphinx 'make build' to generate docs and then show in browser)
    "--type=" "Type of docs to compile"
    "--verbose" "Display verbose output"

**pre_django**  (Installs requirements and cleans previous python compiled files)

**compile_coffeescript** (Compiles Coffeescript files)
    "--system=" "System to act on e.g. lms, cms"
    "--env=" "Environment settings e.g. aws, dev"
    "--watch" "Run with watch"
    "--debug" "Run with debug"
    "--clobber" "Remove compiled Coffeescript files"

**compile_sass** (Compiles Sass files)
    "--system=" "System to act on e.g. lms, cms"
    "--env=" "Environment settings e.g. aws, dev"
    "--watch" "Run with watch"
    "--debug" "Run with debug"

**compile_xmodule** (Compiles Xmodule)
    "--system=" "System to act on e.g. lms, cms"
    "--env=" "Environment settings e.g. aws, dev"
    "--watch" "Run with watch"
    "--debug" "Run with debug"

**compile_assets** (Compiles Coffeescript, Sass, Xmodule and optionally runs collectstatic)
    "--system=" "System to act on e.g. lms, cms"
    "--env=" "Environment settings e.g. aws, dev"
    "--watch" "Run with watch"
    "--debug" "Run with debug"
    "--collectstatic" "Runs collectstatic

**lms** (runs lms)
    "--env=" "Environment settings e.g. aws, dev"

**cms** (runs cms)
    "--env=" "Environment settings e.g. aws, dev"

**run_server** (run a specific server)
    "--system=" "System to act on e.g. lms, cms"
    "--env=" "Environment settings e.g. aws, dev"

**resetdb** (runs syncdb and then migrate)
    "--env=" "Environment settings e.g. aws, dev"

**check_settings** (checks settings files)
    "--env=" "Environment settings e.g. aws, dev"

**run_all_servers** (runs lms and cms)
    "--env=" "Environment settings e.g. aws, dev"
    "--worker_env=" "Environment settings for celery workers"
    "--logfile=" "File to log output to"

**run_celery** (runs celery for specified system)
    "--system=" "System to act on e.g. lms, cms"
    "--env=" "Environment settings e.g. aws, dev"
