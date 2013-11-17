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

**compile_assets**
    "--system=" "System to act on e.g. lms,cms"
    "--env=" "Environment settings e.g. aws, dev"
    "--w" "Run with watch"
    "--d" "Run with debug"

**fast_lms** (runs lms without running prereqs)
**run_server** (run a specific server)
    "--system=" "System to act on e.g. lms,cms"
    "--env=" "Environment settings e.g. aws, dev"

**resetdb** (runs syncdb and then migrate)
    "--env=" "Environment settings e.g. lms,cms"

**check_settings** (checks settings files)
    "--env=" "Environment settings e.g. lms,cms"

**run_all_servers** (runs lms and cms)
    "--env=" "Environment settings e.g. lms,cms"