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
   need to install the requirements from requirements/edx-sandbox::

    $ pip install -r requirements/edx-sandbox/base.txt

2. At the instruction to create the AppArmor profile, you'll need a line in
   the profile for the sandbox packages.  <EDXPLATFORM> is the full path to
   your edx_platform repo::

    <EDXPLATFORM>/common/lib/sandbox-packages/** r,

3. You can configure resource limits in settings.py.  A CODE_JAIL setting is
   available, a dictionary.  The "limits" key lets you adjust the limits for
   CPU time, real time, and memory use.  Setting any of them to zero disables
   that limit::

    # in settings.py...
    CODE_JAIL = {
        # Configurable limits.
        'limits': {
            # How many CPU seconds can jailed code use?
            'CPU': 1,
            # How many real-time seconds will a sandbox survive?
            'REALTIME': 1,
            # How much memory (in bytes) can a sandbox use?
            'VMEM': 30000000,
        },
    }


That's it.  Once you've finished the CodeJail configuration instructions,
your course-hosted Python code should be run securely.
