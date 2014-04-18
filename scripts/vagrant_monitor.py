#!/usr/bin/env python
"""
Automatically start and stop your vagrant instance on OS X (tested on 10.9).


Copy vagrantmonitor.plist to ~/Library/LaunchAgents/ and replace PATH_TO to
the absolute path to the edx-platform parent directory.
Then reboot or "launchctl load ~/Library/LaunchAgents/vagrantmonitor.plist"
On logout, this script will suspend the vagrant instance.

In order for vagrant to add shared folders without prompting for a password,
add this to /etc/sudoers

Cmnd_Alias VAGRANT_EXPORTS_ADD = /usr/bin/su root -c echo '*' >> /etc/exports
Cmnd_Alias VAGRANT_NFSD = /sbin/nfsd restart
Cmnd_Alias VAGRANT_EXPORTS_REMOVE = /usr/bin/sed -e /*/ d -ibak /etc/exports
%staff ALL=(root) NOPASSWD: VAGRANT_EXPORTS_ADD, VAGRANT_NFSD, VAGRANT_EXPORTS_REMOVE

"""
import subprocess
import signal
import os
import os.path
import time
import sys


def vagrant_up():
    subprocess.call(['vagrant', 'up'])

def vagrant_suspend(signum, frame):
    subprocess.call(['vagrant', 'suspend'])
    sys.exit()

def wait():
    signal.signal(signal.SIGTERM, vagrant_suspend)
    try:
        signal.pause()
    except KeyboardInterrupt:
        vagrant_suspend(None, None)


if __name__ == '__main__':
    fname = os.path.abspath(__file__)
    parent = os.path.dirname(os.path.dirname(os.path.dirname(fname)))
    os.chdir(parent)

    vagrant_up()

    wait()
