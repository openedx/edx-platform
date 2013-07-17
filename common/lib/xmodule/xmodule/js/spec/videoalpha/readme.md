Jasmine JavaScript tests status
-------------------------------

As of 18.07.2013, 12:55, each individual tests file in this directory passes. However,
if you try to run all of them at the same time, weird things start to happen. In some
cases the browser crashes, in other cases there are failing tests with extremely crazy
failing messages.

I [Valera Rozuvan] believe that this is due to the fact that almost in every file there
is present the function initialize() which is invoked many-many-many times throughout
the file. With each invocation, initialize() instantiates a new VideoAlpha instance.
It shouoldn't be necessary to instantiate a new VideoAlpha instance for each it() test.
Many it() tests can be run in sequence on the same VideoAlpha instance - it is just a
matter of correctly planning the order in which the it() tests are run.

So, you can do either:

    a.) Run tests individually, changing in each file the top level "xdescribe(" to
    "describe(". Make sure that you change it back to "xdescribe(" once you are done.

    b.) Refactor all the VideoAlpha tests so that they can be run all at once.

Good luck ^_^v (and thanks for all the fish!)



PS: When you are running the tests in chrome locally, make sure that chrome is started
with the option "--allow-file-access-from-files".

PPS: Don't forget to place test video files (test.mp4, test.ogv, test.webm) into the
folder "common/lib/xmodule". You can get these from http://www.quirksmode.org/html5/tests/video.html
or from some other site that demonstrates HTML5 video playback. Just open up the site's
source, and save the video files (make sure to rname them to "test.*").
