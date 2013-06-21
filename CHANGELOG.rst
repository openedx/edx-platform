Change Log
----------

These are notable changes in edx-platform.  This is a rolling list of changes,
in roughly chronological order, most recent first.  Add your entries at or near
the top.  Include a label indicating the component affected.

Studio: Remove XML from the video component editor. All settings are
moved to be edited as metadata.

XModule: Only write out assets files if the contents have changed.

XModule: Don't delete generated xmodule asset files when compiling (for
instance, when XModule provides a coffeescript file, don't delete
the associated javascript)

Studio: For courses running on edx.org (marketing site), disable fields in
Course Settings that do not apply.

Common: Make asset watchers run as singletons (so they won't start if the
watcher is already running in another shell).

Common: Use coffee directly when watching for coffeescript file changes.

Common: Make rake provide better error messages if packages are missing.

Common: Repairs development documentation generation by sphinx.

LMS: Problem rescoring.  Added options on the Grades tab of the
Instructor Dashboard to allow all students' submissions for a
particular problem to be rescored.  Also supports resetting all
students' number of attempts to zero.  Provides a list of background
tasks that are currently running for the course, and an option to
see a history of background tasks for a given problem.

LMS: Fixed the preferences scope for storing data in xmodules.

LMS: Forums.  Added handling for case where discussion module can get `None` as
value of lms.start in `lms/djangoapps/django_comment_client/utils.py`

Studio, LMS: Make ModelTypes more strict about their expected content (for
instance, Boolean, Integer, String), but also allow them to hold either the
typed value, or a String that can be converted to their typed value. For example,
an Integer can contain 3 or '3'. This changed an update to the xblock library.

LMS: Courses whose id matches a regex in the COURSES_WITH_UNSAFE_CODE Django
setting now run entirely outside the Python sandbox.

Blades: Added tests for Video Alpha player.

Blades: Video Alpha bug fix for speed changing to 1.0 in Firefox.

Blades: Additional event tracking added to Video Alpha: fullscreen switch, show/hide
captions.

CMS: Allow editors to delete uploaded files/assets

XModules: `XModuleDescriptor.__init__` and `XModule.__init__` dropped the
`location` parameter (and added it as a field), and renamed `system` to `runtime`,
to accord more closely to `XBlock.__init__`

LMS: Some errors handling Non-ASCII data in XML courses have been fixed.

LMS: Add page-load tracking using segment-io (if SEGMENT_IO_LMS_KEY and
SEGMENT_IO_LMS feature flag is on)

Blades: Simplify calc.py (which is used for the Numerical/Formula responses); add trig/other functions.

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

Common: all dates and times are not time zone aware datetimes. No code should create or use struct_times nor naive
datetimes.

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

Studio: Autoplay for Video Alpha is disabled (only in Studio).

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

