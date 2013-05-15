Configuring Capa sandboxed execution
====================================

Capa problems can contain code authored by the course author.  We need to
execute that code in a sandbox.  We use CodeJail as the sandboxing facility,
but it needs to be configured specifically for Capa's use.

As a developer, you don't have to do anything to configure sandboxing if you
don't want to, and everything will operate properly, you just won't have
protection on that code.

If you want to configure sandboxing, you're going to use the `README from
CodeJail`__, with a few customized tweaks.

__ https://github.com/edx/codejail/blob/master/README.rst


1. At the instruction to install packages into the sandboxed code, you'll 
   need to install both `pre-sandbox-requirements.txt` and 
   `sandbox-requirements.txt`::

    $ sudo pip install -r pre-sandbox-requirements.txt
    $ sudo pip install -r sandbox-requirements.txt

2. At the instruction to create the AppArmor profile, you'll need a line in
   the profile for the sandbox packages.  <EDXPLATFORM> is the full path to
   your edx_platform repo::

    <EDXPLATFORM>/common/lib/sandbox-packages/** r,

That's it.  Once you've finished the CodeJail configuration instructions,
your course-hosted Python code should be run securely.
