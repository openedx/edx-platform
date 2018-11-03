.. _changelog:

Changelog
=========

A summary of changes to nbgrader.

0.5.x
-----

0.5.4
~~~~~

nbgrader version 0.5.3 is a bugfix release, with the following PRs merged:

- PR #898: Make sure validation is run in the correct directory
- PR #895: Add test and fix for parsing csv key names with spaces
- PR #888: Fix overwritekernelspec preprocessor and update tests
- PR #880: change directory when validating notebooks
- PR #873: Fix issue with student dictionaries when assignments have zero points

Thanks to the following users who submitted PRs or reported issues that were fixed for the 0.5.4 release:

- jcsutherland
- jhamrick
- lgpage
- misolietavec
- mpacer
- ncclementi
- randy3k

0.5.3
~~~~~

nbgrader version 0.5.3 is a bugfix release, with the following PRs merged:

- PR #868: Fix travis to work with trusty
- PR #867: Change to the root of the course directory before running nbgrader converters
- PR #866: Set nbgrader url prefix to be relative to notebook_dir
- PR #865: Produce warnings if the exchange isn't set up correctly
- PR #864: Fix link to jupyterhub docs
- PR #861: fix the html to ipynb in docs

Thanks to the following users who submitted PRs or reported issues that were fixed for the 0.5.3 release:

- jhamrick
- misolietavec
- mpacer
- rdpratti

0.5.2
~~~~~

nbgrader version 0.5.2 is a bugfix release, with most of the bugs being discovered and subsequently fixed by the sprinters at SciPy 2017! The following PRs were merged:

- PR #852: Fix spelling wordlist, again
- PR #850: Include extension with feedback template filename
- PR #848: Add links to the scipy talk
- PR #847: Fix html export config options to avoid warnings
- PR #846: Disallow negative point values
- PR #845: Don't install assignment list on windows
- PR #844: Reveal ids if names aren't set
- PR #843: Update spelling wordlist
- PR #840: Avoid extension errors when exchange is missing
- PR #839: Always raise on convert failure
- PR #837: Report mismatch extension versions
- PR #836: Add documentation for course_id and release
- PR #835: DOC: correct Cell Toolbar location
- PR #833: Include quickstart .ipynb header
- PR #831: Fix typo on Managing assignment docs
- PR #830: Print out app subcommands by default
- PR #825: Add directory structure example
- PR #824: Add FAQ sections
- PR #823: Typo fix.
- PR #819: Update install instructions
- PR #816: Add jupyter logo
- PR #802: Fix bug with autograding when there is no timestamp

Thanks to the following users who submitted PRs or reported issues that were fixed for the 0.5.2 release:

- arcticbarra
- BjornFJohansson
- hetland
- ixjlyons
- jhamrick
- katyhuff
- ksunden
- lgpage
- ncclementi
- Ruin0x11

0.5.1
~~~~~

nbgrader version 0.5.1 is a bugfix release mainly fixing an issue with the
formgrader. The following PRs were merged:

- PR #792: Make sure relative paths to source and release dirs are correct
- PR #791: Use the correct version number in the docs

0.5.0
~~~~~

nbgrader version 0.5.0 is another very large release with some very exciting new features! The highlights include:

- The formgrader is now an extension to the notebook, rather than a standalone service.
- The formgrader also includes functionality for running ``nbgrader assign``, ``nbgrader release``, ``nbgrader collect``, and ``nbgrader autograde`` directly from the browser.
- A new command ``nbgrader zip_collect``, which helps with collecting assignment files downloaded from a LMS.
- Hidden test cases are now supported.
- A lot of functionality has moved into standalone objects that can be called directly from Python, as well as a high-level Python API in ``nbgrader.apps.NbGraderAPI`` (see :doc:`/api/high_level_api`).
- A new **Validate** notebook extension, which allows students to validate an assignment notebook from the notebook itself (this is equivalent functionality to the "Validate" button in the Assignment List extension, but without requiring students to be using the Assignment List).
- A new command ``nbgrader db upgrade``, which allows you to migrate your nbgrader database to the latest version without having to manually execute SQL commands.
- New cells when using the Create Assignment extension will automatically given randomly generated ids, so you don't have to set them yourself.
- You can assign extra credit when using the formgrader.

**Important**: Users updating from 0.4.x to 0.5.0 should be aware that they
will need to update their nbgrader database using ``nbgrader db upgrade``
and will need to reinstall the nbgrader extensions (see
:doc:`/user_guide/installation`). Additionally, the configuration necessary to
use the formgrader with JupyterHub has changed, though it is now much more straightforward (see :doc:`/configuration/jupyterhub_config`).

The full list of merged PRs includes:

- PR #789: Fix more inaccurate nbextension test failures after reruns
- PR #788: Fix inaccurate nbextension test failures after reruns
- PR #787: Fix slow API calls
- PR #786: Update documentation for nbgrader as a webapp
- PR #784: Fix race condition in validate extension tests
- PR #782: Implement nbgrader as a webapp
- PR #781: Assign missing notebooks a score of zero and mark as not needing grading
- PR #780: Create a new high-level python API for nbgrader
- PR #779: Update the year!
- PR #778: Create and set permissions for exchange directory when using ``nbgrader release``
- PR #774: Add missing config options
- PR #772: Standalone versions of nbgrader assign, autograde, and feedback
- PR #771: Fix mathjax rendering
- PR #770: Better cleanup when nbconvert-based apps crash
- PR #769: Fix nbgrader validate globbing for real this time
- PR #768: Extra credit
- PR #766: Make sure validation works with notebook globs
- PR #764: Migrate database with alembic
- PR #762: More robust saving of the notebook in create assignment tests
- PR #761: Validate assignment extension
- PR #759: Fix nbextension tests
- PR #758: Set random cell ids
- PR #756: Fix deprecations and small bugs
- PR #755: Fast validate
- PR #754: Set correct permissions when submitting assignments
- PR #752: Add some more informative error messages in zip collect
- PR #751: Don't create the gradebook database until formgrader is accessed
- PR #750: Add documentation for how to pass numeric ids
- PR #747: Skip over students with empty submissions
- PR #746: Fix bug with --to in custom exporters
- PR #738: Refactor the filtering of existing submission notebooks for formgrader
- PR #735: Add DataTables functionality to existing formgrade tables
- PR #732: Fix the collecting of submission files for multiple attempts of multiple notebook assignments
- PR #731: Reset late submission penalty before checking if submission is late or not
- PR #717: Update docs regarding solution delimeters
- PR #714: Preserve kernelspec when autograding
- PR #713: Use new exchange functionality in assignment list app
- PR #712: Move exchange functionality into non-application classes
- PR #711: Move some config options into a CourseDirectory object.
- PR #709: Fix formgrader tests link for 0.4.x branch (docs)
- PR #707: Force rerun nbgrader commands
- PR #704: Fix nbextension tests
- PR #701: Set proxy-type=none in phantomjs
- PR #700: use check_call for extension installation in tests
- PR #698: Force phantomjs service to terminate in Linux
- PR #696: Turn the gradebook into a context manager
- PR #695: Use sys.executable when executing nbgrader
- PR #693: Update changelog from 0.4.0
- PR #681: Hide tests in "Autograder tests" cells
- PR #622: Integrate the formgrader into the notebook
- PR #526: Processing of LMS downloaded submission files

Thanks to the following contributors who submitted PRs or reported issues that were merged/closed for the 0.5.0 release:

- AnotherCodeArtist
- dementrock
- dsblank
- ellisonbg
- embanner
- huwf
- jhamrick
- jilljenn
- lgpage
- minrk
- suchow
- Szepi
- whitead
- ZelphirKaltstahl
- zpincus

0.4.x
-----

0.4.0
~~~~~

nbgrader version 0.4.0 is a substantial release with lots of changes and several new features. The highlights include:

- Addition of a command to modify students and assignments in the database (``nbgrader db``)
- Validation of nbgrader metadata, and a command to automatically upgrade said metadata from the previous version (``nbgrader update``)
- Support for native Jupyter nbextension and serverextension installation, and deprecation of the ``nbgrader nbextension`` command
- Buttons to reveal students' names in the formgrader
- Better reporting of errors and invalid submissions in the "Assignment List" extension
- Addition of a menu to change between different courses in the "Assignment List" extension
- Support to run the formgrader as an official JupyterHub service
- More flexible code and text stubs when creating assignments
- More thorough documentations

**Important**: Users updating from 0.3.x to 0.4.0 should be aware that they
will need to update the metadata in their assignments using ``nbgrader update``
and will need to reinstall the nbgrader extensions (see
:doc:`/user_guide/installation`). Additionally, the configuration necessary to
use the formgrader with JupyterHub has changed, though it is now much less
brittle (see :doc:`/configuration/jupyterhub_config`).

The full list of merged PRs includes:

- PR #689: Add cwd to path for all nbgrader apps
- PR #688: Make sure the correct permissions are set on released assignments
- PR #687: Add display_data_priority option to GetGrades preprocessor
- PR #679: Get Travis-CI to build
- PR #678: JUPYTERHUB_SERVICE_PREFIX is already the full URL prefix
- PR #672: Undeprecate --create in assign and autograde
- PR #670: Fix deprecation warnings for config options
- PR #665: Preventing URI Encoding of the base-url in the assignment_list extension
- PR #656: Update developer installation docs
- PR #655: Fix saving notebook in create assignment tests
- PR #652: Make 0.4.0 release
- PR #651: Update changelog with changes from 0.3.3 release
- PR #650: Print warning when no config file is found
- PR #649: Bump the number of test reruns even higher
- PR #646: Fix link to marr paper
- PR #645: Fix coverage integration by adding codecov.yml
- PR #644: Add AppVeyor CI files
- PR #643: Add command to update metadata
- PR #642: Handle case where points is an empty string
- PR #639: Add and use a Gradebook contextmanager for DbApp and DbApp tests
- PR #637: Update conda channel to conda-forge
- PR #635: Remove conda recipe and document nbgrader-feedstock
- PR #633: Remove extra level of depth in schema per @ellisonbg
- PR #630: Don't fail ``test_check_version`` test on ``'import sitecustomize' failed error``
- PR #629: Update changelog for 0.3.1 and 0.3.2
- PR #628: Make sure to include schema files
- PR #625: Add "nbgrader db" app for modifying the database
- PR #623: Move server extensions into their own directory
- PR #621: Replace tabs with spaces in installation docs
- PR #620: Document when needs manual grade is set
- PR #619: Add CI tests for python 3.6
- PR #618: Implement formgrader as a jupyterhub service
- PR #617: Add ability to show student names in formgrader
- PR #616: Rebuild docs
- PR #615: Display assignment list errors
- PR #614: Don't be as strict about solution delimeters
- PR #613: Update FAQ with platform information
- PR #612: Update to new traitlets syntax
- PR #611: Add metadata schema and documentation
- PR #610: Clarify formgrader port and suppress notebook output
- PR #607: Set instance variables in base auth class before running super init
- PR #598: Conda recipe - nbextension link / unlink scripts
- PR #597: Re-submitting nbextension work from previous PR
- PR #594: Revert "Use jupyter nbextension/serverextension for installation/activation"
- PR #591: Test empty and invalid timestamp strings
- PR #590: Processing of invalid ``notebook_id``
- PR #585: Add catches for empty timestamp files and invalid timestamp strings
- PR #581: Update docs with invoke test group commands
- PR #571: Convert readthedocs links for their .org -> .io migration for hosted projects
- PR #567: Handle autograding failures better
- PR #566: Add support for true read-only cells
- PR #565: Add option to nbgrader fetch for replacing missing files
- PR #564: Update documentation pertaining to the assignment list extension
- PR #563: Add ability to switch between courses in assignment list extension
- PR #562: Add better support to transfer apps for multiple courses
- PR #550: Add documentation regarding how validation works
- PR #545: Document how to customize the student version of an assignment
- PR #538: Use official HubAuth from JupyterHub
- PR #536: Create a "nbgrader export" command
- PR #523: Allow code stubs to be language specific

Thanks to the following contributors who submitted PRs or reported issues that were merged/closed for the 0.4.0 release:

- adamchainz
- AstroMike
- ddbourgin
- dlsun
- dsblank
- ellisonbg
- huwf
- jhamrick
- lgpage
- minrk
- olgabot
- randy3k
- whitead
- whositwhatnow
- willingc

0.3.x
-----

0.3.3
~~~~~

Version 0.3.3 of nbgrader is a minor bugfix release that fixes an issue with
running ``nbgrader fetch`` on JupyterHub. The following PR was merged for the 0.3.3 milestone:

- PR #600: missing sys.executable, "-m", on fetch_assignment

Thanks to the following contributors who submitted PRs or reported issues that were merged/closed for the 0.3.3 release:

- alikasamanli
- hetland

0.3.2
~~~~~

Version 0.3.2 of nbgrader includes a few bugfixes pertaining to building nbgrader on conda-forge.

- PR #608: Fix Windows tests
- PR #601: Add shell config for invoke on windows
- PR #593: Send xsrf token in the X-XSRF-Token header for ajax
- PR #588: ``basename`` to wordslist
- PR #584: Changes for Notebook v4.3 tests

Thanks to lgpage, who made all the changes necessary for the 0.3.2 release!

0.3.1
~~~~~

Version 0.3.1 of nbgrader includes a few bugfixes pertaining to PostgreSQL and
updates to the documentation. The full list of merged PRs is:

- PR #561: Close db engine
- PR #548: Document how to install the assignment list extension for all users
- PR #546: Make it clearer how to set due dates
- PR #535: Document using JupyterHub with SSL
- PR #534: Add advanced topics section in the docs
- PR #533: Update docs on installing extensions

Thanks to the following contributors who submitted PRs or reported issues that were merged/closed for the 0.3.1 release:

- ddbourgin
- jhamrick
- whositwhatnow

0.3.0
~~~~~

Version 0.3.0 of nbgrader introduces several significant changes. Most notably,
this includes:

- Windows support
- Support for Python 3.5
- Support for Jupyter Notebook 4.2
- Allow assignments and students to be specified in ``nbgrader_config.py``
- Addition of the "nbgrader quickstart" command
- Addition of the "nbgrader extension uninstall" command
- Create a nbgrader conda recipe
- Add an entrypoint for late penalty plugins

The full list of merged PRs is:

- PR #521: Update to most recent version of invoke
- PR #512: Late penalty plugin
- PR #510: Fix failing windows tests
- PR #508: Run notebook/formgrader/jupyterhub on random ports during tests
- PR #507: Add a FAQ
- PR #506: Produce a warning if no coverage files are produced
- PR #505: Use .utcnow() rather than .now()
- PR #498: Add a section on autograding wisdom
- PR #495: Raise an error on iopub timeout
- PR #494: Write documentation on creating releases
- PR #493: Update nbgrader to be compatible with notebook version 4.2
- PR #492: Remove generate_hubapi_token from docs
- PR #490: Temporarily pin to notebook 4.1
- PR #489: Make sure next/prev buttons use correct base_url
- PR #486: Add new words to wordlist
- PR #485: Update README gif links after docs move into nbgrader
- PR #477: Create a conda recipe
- PR #473: More helpful default comment box message
- PR #470: Fix broken links
- PR #467: unpin jupyter-client
- PR #466: Create nbgrader quickstart command
- PR #465: Confirm no SSL when running jupyterhub
- PR #464: Speed up tests
- PR #461: Add more prominent links to demo
- PR #460: Test that other kernels work with nbgrader
- PR #458: Add summary and links to resources in docs
- PR #457: Update formgrader options to not conflict with the notebook
- PR #455: More docs
- PR #454: Simplify directory and notebook names
- PR #453: Merge user guide into a few files
- PR #452: Improve docs reliability
- PR #451: Execute documentation notebooks manually
- PR #449: Allow --assignment flag to be used with transfer apps
- PR #448: Add --no-execute flag to autogradeapp.py
- PR #447: Remove option to generate the hubapi token
- PR #446: Make sure perms are set correctly by nbgrader submit
- PR #445: Skip failures and log to file
- PR #444: Fix setup.py
- PR #443: Specify assignments and students in the config file
- PR #442: Fix build errors
- PR #430: Reintroduce flit-less setup.py
- PR #425: Enable 3.5 on travis.
- PR #421: Fix Contributor Guide link
- PR #414: Restructure user guide TOC and doc flow to support new users
- PR #413: Windows support
- PR #411: Add tests for https
- PR #409: Make a friendlier development install
- PR #408: Fix formgrader to use course directory
- PR #407: Add --no-metadata option to nbgrader assign
- PR #405: nbgrader release typo
- PR #402: Create a Contributor Guide in docs
- PR #397: Port formgrader to tornado
- PR #395: Specify root course directory
- PR #387: Use sys.executable to run suprocesses
- PR #386: Use relative imports
- PR #384: Rename the html directory to formgrader
- PR #381: Access notebook server of formgrader user

Thanks to the following contributors who submitted PRs or reported issues that were merged/closed for the 0.3.0 release:

- alchemyst
- Carreau
- ellisonbg
- ischurov
- jdfreder
- jhamrick
- jklymak
- joschu
- lgpage
- mandli
- mikebolt
- minrk
- olgabot
- sansary
- svurens
- vinaykola
- willingc

0.2.x
-----

0.2.2
~~~~~

Adds some improvements to the documentation and fixes a few small bugs:

- Add requests as a dependency
- Fix a bug where the "Create Assignment" extension was not rendering correctly in Safari
- Fix a bug in the "Assignment List" extension when assignment names had periods in them
- Fix integration with JupyterHub when SSL is enabled
- Fix a bug with computing checksums of cells that contain UTF-8 characters under Python 2

0.2.1
~~~~~

Fixes a few small bugs in v0.2.0:

- Make sure checksums can be computed from cells containing unicode characters
- Fixes a bug where nbgrader autograde would crash if there were any cells with blank grade ids that weren't actually marked as nbgrader cells (e.g. weren't tests or read-only or answers)
- Fix a few bugs that prevented postgres from being used as the database for nbgrader

0.2.0
~~~~~

Version 0.2.0 of nbgrader primarily adds support for version 4.0 of the Jupyter notebook and associated project after The Big Split. The full list of major changes are:

- Jupyter notebook 4.0 support
- Make it possible to run the formgrader inside a Docker container
- Make course_id a requirement in the transfer apps (list, release, fetch, submit, collect)
- Add a new assignment list extension which allows students to list, fetch, validate, and submit assignments from the notebook dashboard interface
- Auto-resize text boxes when giving feedback in the formgrader
- Deprecate the BasicConfig and NbGraderConfig classes in favor of a NbGrader class

Thanks to the following contributors who submitted PRs or reported issues that were merged/closed for the 0.2.0 release:

- alope107
- Carreau
- ellisonbg
- jhamrick
- svurens

0.1.0
-----

I'm happy to announce that the first version of nbgrader has (finally) been released! nbgrader is a tool that I've been working on for a little over a year now which provides a suite of tools for creating, releasing, and grading assignments in the Jupyter notebook. So far, nbgrader has been used to grade assignments for the class I ran in the spring, as well as two classes that Brian Granger has taught.

If you have any questions, comments, suggestions, etc., please do open an issue on the bugtracker. This is still a very new tool, so I am sure there is a lot that can be improved upon!

Thanks so much to all of the people who have contributed to this release by reporting issues and/or submitting PRs:

- alope107
- Carreau
- ellachao
- ellisonbg
- ivanslapnicar
- jdfreder
- jhamrick
- jonathanmorgan
- lphk92
- redSlug
- smeylan
- suchow
- svurens
- tasilb
- willingc
