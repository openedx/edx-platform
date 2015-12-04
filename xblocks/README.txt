This is a directory for holding third party XBlocks not included with
edx-platform. This is helpful since this directory is shared with
vagrant in the edX vagrant, and so it is a good place to keep these
while developing.

There is a script which will grab many of the known XBlocks (but not
install them). To install them, run 'python setup.py develop' from
within vagrant (not on the host machine).

Be aware most of the XBlocks in this script were developed by third
parties, and have not been reviewed by edX:

* We have not audited the source code for security. 
* We have no audited the code for scaling, robustness, or
  compatibility with future versions of edX.

Please be very aware of security issues with running programs (these
and others) from untrusted locations. Before running something which
manages learner data, you'll want to either:

1. Make sure you either trust the author (for example, running
   edX-developed prototype XBlocks is probably okay, as is from some
   of the major companies around the edX ecosystem)
2. Have looked over the source code to make sure something malicious
   isn't going on. In most cases, this is pretty fast.

Listing in the file (or lack thereof) isn't any sort of
endorsement. This is what we could find on the internet on a quick
skim. In some cases, there are variants of the same XBlock in multiple
git repos. In such cases, the choice of which one we included was
nearly random (we did a quick skim to either get the one others forked
from, most recent commits, or whichever one first came up on
Google). If you see missing XBlocks, incorrect/non-canonical forks,
etc., please make a pull request to fix it.

Grabbing all of these XBlocks will use nearly a gig of disk
space. Installing all of them will most likely result in an unstable
system -- a few are prototypes, or require external services to work.
