Jasmine JavaScript tests status
-------------------------------

As of 22.07.2013, all the tests in this directory pass. To disable each of them, change the top level "describe(" to "xdescribe(".

PS: When you are running the tests in chrome locally, make sure that chrome is started
with the option "--allow-file-access-from-files".

PPS: Don't forget to place test video files (test.mp4, test.ogv, test.webm) into the
folder "common/lib/xmodule". You can get these from http://www.quirksmode.org/html5/tests/video.html
or from some other site that demonstrates HTML5 video playback. Just open up the site's
source, and save the video files (make sure to rname them to "test.*").
