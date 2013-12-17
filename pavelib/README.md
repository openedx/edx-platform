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

**pre_django**  (Installs requirements and cleans previous python compiled files)

**compile_coffeescript**
    "--system=" "System to act on e.g. lms, cms"
    "--env=" "Environment settings e.g. aws, dev"
    "--watch" "Run with watch"
    "--debug" "Run with debug"
    "--clobber" "Remove compiled Coffeescript files"

**compile_sass**
    "--system=" "System to act on e.g. lms, cms"
    "--env=" "Environment settings e.g. aws, dev"
    "--watch" "Run with watch"
    "--debug" "Run with debug"

**compile_xmodule**
    "--system=" "System to act on e.g. lms, cms"
    "--env=" "Environment settings e.g. aws, dev"
    "--watch" "Run with watch"
    "--debug" "Run with debug"

**compile_assets**
    "--system=" "System to act on e.g. lms, cms"
    "--env=" "Environment settings e.g. aws, dev"
    "--watch" "Run with watch"
    "--debug" "Run with debug"
    "--collectstatic" "Runs collectstatic


**pre_django** (installs python rereqs)


**fast_lms** (runs lms without running prereqs)

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

**run_celery** (runs celery for specified system)
    "--system=" "System to act on e.g. lms, cms"