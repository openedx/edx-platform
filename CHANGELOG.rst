Change Log
----------

These are notable changes in edx-platform.  This is a rolling list of changes,
in roughly chronological order, most recent first.  Add your entries at or near
the top.  Include a label indicating the component affected.


LMS: Some errors handling Non-ASCII data in XML courses have been fixed.

LMS: Add page-load tracking using segment-io (if SEGMENT_IO_LMS_KEY and
SEGMENT_IO_LMS feature flag is on)

LMS: Background colors on login, register, and courseware have been corrected
back to white.

LMS: Accessibility improvements have been made to several courseware and
navigation elements.

LMS: Small design/presentation changes to login and register views.

LMS: Functionality added to instructor enrollment tab in LMS such that invited
student can be auto-enrolled in course or when activating if not current
student.

Blades: Staff debug info is now accessible for Graphical Slider Tool problems.

Blades: For Video Alpha the events ready, play, pause, seek, and speed change
are logged on the server (in the logs). 

Common: Developers can now have private Django settings files.

Common: Safety code added to prevent anything above the vertical level in the
course tree from being marked as version='draft'. It will raise an exception if
the code tries to so mark a node. We need the backtraces to figure out where
this very infrequent intermittent marking was occurring. It was making courses
look different in Studio than in LMS.

Deploy: MKTG_URLS is now read from env.json.

Common: Theming makes it possible to change the look of the site, from
Stanford.

Common: Accessibility UI fixes.

Common: The "duplicate email" error message is more informative.

Studio: Component metadata settings editor.

Studio: Autoplay is disabled (only in Studio).

Studio: Single-click creation for video and discussion components.

Studio: fixed a bad link in the activation page.

LMS: Changed the help button text.

LMS: Fixed failing numeric response (decimal but no trailing digits).

LMS: XML Error module no longer shows students a stack trace.

Blades: Videoalpha.

XModules: Added partial credit for foldit module.

XModules: Added "randomize" XModule to list of XModule types.

XModules: Show errors with full descriptors.

XQueue: Fixed (hopefully) worker crash when the connection to RabbitMQ is
dropped suddenly.

XQueue: Upload file submissions to a specially named bucket in S3.

Common: Removed request debugger.

Common: Updated Django to version 1.4.5.

Common: Updated CodeJail.

Common: Allow setting of authentication session cookie name.

