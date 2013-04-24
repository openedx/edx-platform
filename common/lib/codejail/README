CodeJail
========

CodeJail manages execution of untrusted code in secure sandboxes. It is
designed primarily for Python execution, but can be used for other languages as
well.

Security is enforced with AppArmor.  If your operating system doesn't support
AppArmor, then CodeJail won't protect the execution.

CodeJail is designed to be configurable, and will auto-configure itself for
Python execution if you install it properly.  The configuration is designed to
be flexible: it can run in safe more or unsafe mode.  This helps support large
development groups where only some of the developers are involved enough with
secure execution to configure AppArmor on their development machines.

If CodeJail is not configured for safe execution, it will execution Python
using the same API, but will not guard against malicious code.  This allows the
same code to be used on safe-configured or non-safe-configured developer's
machines.


Installation
------------

These instructions detail how to configure your operating system so that
CodeJail can execute Python code safely.  You can run CodeJail without these
steps, and you will have an unsafe CodeJail.  This is fine for developers'
machines who are unconcerned with security, and simplifies the integration of
CodeJail into your project.

To secure Python execution, you'll be creating a new virtualenv.  This means
you'll have two: the main virtualenv for your project, and the new one for
sandboxed Python code.

Choose a place for the new virtualenv, call it <SANDENV>.  It will be
automatically detected and used if you put it right alongside your existing
virtualenv, but with -sandbox appended.  So if your existing virtualenv is in
~/ve/myproj, make <SANDENV> be ~/ve/myproj-sandbox (but you'll need to spell
out your home directory instead of ~).

Other details here that depend on your configuration:

    - Your mitx working tree is <MITX>, for example, ~/mitx_all/mitx

    - The user running the LMS is <USER>, for example, you on your dev machine,
      or www-data on a server.

1. Create the new virtualenv::

    $ sudo virtualenv <SANDENV>

2. Install the sandbox requirements::

    $ source <SANDENV>/bin/activate
    $ sudo pip install -r sandbox-requirements.txt

3. Add a sandbox user::

    $ sudo addgroup sandbox
    $ sudo adduser --disabled-login sandbox --ingroup sandbox

4. Let the web server run the sandboxed Python as sandbox.  Create the file
/etc/sudoers.d/01-sandbox::

    $ visudo -f /etc/sudoers.d/01-sandbox

    <USER> ALL=(sandbox) NOPASSWD:<SANDENV>/bin/python
    <USER> ALL=(ALL) NOPASSWD:/bin/kill

5. Edit an AppArmor profile.  The file must be named for the python executable,
but with slashes changed to dots::

    #include <tunables/global>

    <SANDENV>/bin/python {
        #include <abstractions/base>

        <SANDENV>/** mr,
        <MITX>/common/lib/sandbox-packages/** r,
        /usr/local/lib/python2.7/** r,
        /usr/lib/python2.7/** rix,

        /tmp/** rix,
    }

6. Parse the profiles::

    $ sudo apparmor_parser <APPARMOR_FILE>

7. Reactivate your project's main virtualenv again.


Tests
=====

The tests run under nose in the standard fashion.

If CodeJail is running unsafely, many of the tests will be automatically
skipped, or will fail, depending on whether CodeJail thinks it should be in
safe mode or not.
