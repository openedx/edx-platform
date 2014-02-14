Developer Workspace Migrations
==============================

This directory contains executable files which run once prior to
installation of pre-requisites to bring a developers workspace
into line.

Specifications
--------------

Each file in this directory should meet the following criteria

* Executable (`chmod +x ws_migrations/foo.sh`)
* Idempotent (ideally, each script is run only once, but no
  guarantees are made by the caller, so the script must do
  the right thing)
* Either fast or verbose (if the script is going to take
  a long time, it should notify the user of that)
* A comment at the top of the file explaining the migration

Execution
---------

The scripts are run by the rake task `ws:migrate`. That task
only runs a given script if a corresponding marker file
in .completed-ws-migrations doesn't already exist.

If the SKIP_WS_MIGRATIONS environment variable is set, then
no workspace migrations will be run.