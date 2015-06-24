Change Log
----------

These are notable changes in edx-platform.  This is a rolling list of changes,
in roughly chronological order, most recent first.  Add your entries at or near
the top.  Include a label indicating the component affected.

Studio/LMS: Implement cohorted courseware. TNL-648

LMS: Student Notes: Eventing for Student Notes. TNL-931

LMS: Student Notes: Add course structure view. TNL-762

LMS: Student Notes: Scroll and opening of notes. TNL-784

LMS: Student Notes: Add styling to Notes page. TNL-932

LMS: Student Notes: Add more graceful error message.

LMS: Student Notes: Toggle all notes TNL-661

LMS: Student Notes: Use JWT ID-Token for authentication annotation requests. TNL-782

LMS: Student Notes: Add possibility to search notes. TNL-731

LMS: Student Notes: Toggle single note visibility. TNL-660

LMS: Student Notes: Add Notes page. TNL-797

LMS: Student Notes: Add possibility to add/edit/remove notes. TNL-655

Platform: Add group_access field to all xblocks.  TNL-670

LMS: Add support for user partitioning based on cohort.  TNL-710

Platform: Add base support for cohorted group configurations.  TNL-649

LMS: Support assigning students to cohorts via a CSV file upload. TNL-735

Common: Add configurable reset button to units

Studio: Add support xblock validation messages on Studio unit/container page. TNL-683

LMS: Support adding cohorts from the instructor dashboard. TNL-162

LMS: Support adding students to a cohort via the instructor dashboard. TNL-163

LMS: Show cohorts on the new instructor dashboard. TNL-161

LMS: Extended hints feature

LMS: Mobile API available for courses that opt in using the Course Advanced
Setting "Mobile Course Available" (only used in limited closed beta).

Studio: Video Module now has an optional advanced setting "EdX Video ID" for
courses where assets are managed entirely by the video team. This is optional
and opt-in (only used in a limited closed beta for now).

LMS: Do not allow individual due dates to be earlier than the normal due date. LMS-6563

Blades: Course teams can turn off Chinese Caching from Studio. BLD-1207

LMS: Instructors can request and see content of previous bulk emails sent in the instructor dashboard.

Studio: New course outline and unit/container pages with revised publishing model. STUD-1790 (part 1)

Studio: Backbone version of the course outline page. STUD-1726.

Studio: New advanced setting "invitation_only" for courses. This setting overrides the enrollment start/end dates
  if set. LMS-2670

LMS: Register button on About page was active even when greyed out. Now made inactive when appropriate and
displays appropriate context sensitive message to student. LMS-2717

Blades: Redirect Chinese students to a Chinese CDN for video. BLD-1052.

Studio: Show display names and help text in Advanced Settings. Also hide deprecated settings
by default.

Studio: Move Peer Assessment into advanced problems menu.

Studio: Support creation and editing of split_test instances (Content Experiments)
entirely in Studio. STUD-1658.

Blades: Add context-aware video index. BLD-933

Blades: Fix bug with incorrect link format and redirection. BLD-1049

Blades: Fix bug with incorrect RelativeTime value after XML serialization. BLD-1060

LMS: Update bulk email implementation to lessen load on the database
by consolidating chunked queries for recipients into a single query.

Blades: Fix link to javascript file in ChoiceTextResponse. BLD-1103.

All: refactored code to handle course_ids, module_ids, etc in a cleaner way.
See https://github.com/edx/edx-platform/wiki/Opaque-Keys for details.

Blades: Remove Video player outline. BLD-975.

Blades: Fix Youtube regular expression in video player editor. BLD-967.

Studio: Support editing of containers. STUD-1312.

Blades: Fix displaying transcripts on touch devices. BLD-1033.

Blades: Tolerance expressed in percentage now computes correctly. BLD-522.

Studio: Support add, delete and duplicate on the container page. STUD-1490.

Studio: Add drag-and-drop support to the container page. STUD-1309.

Common: Add extensible third-party auth module.

Blades: Added new error message that displays when HTML5 video is not supported
altogether. Make sure spinner gets hidden when error message is shown. BLD-638.

LMS: Switch default instructor dashboard to the new (formerly "beta")
  instructor dashboard. Puts the old (now "legacy") dash behind a feature flag.
  LMS-1296

Blades: Handle situation if no response were sent from XQueue to LMS in Matlab
problem after Run Code button press. BLD-994.

Blades: Set initial video quality to large instead of default to avoid automatic
switch to HD when iframe resizes. BLD-981.

Blades: Add an upload button for authors to provide students with an option to
download a handout associated with a video (of arbitrary file format). BLD-1000.

Studio: Add "raw HTML" editor so that authors can write HTML that will not be
changed in any way. STUD-1562

Blades: Show the HD button only if there is an HD version available. BLD-937.

Studio: Add edit button to leaf xblocks on the container page. STUD-1306.

Blades: Add LTI context_id parameter. BLD-584.

Blades: Update LTI resource_link_id parameter. BLD-768.

Blades: Transcript translations should be displayed in their source language (BLD-935).

Blades: Create an upload modal for video transcript translations (BLD-751).

Studio and LMS: Upgrade version of TinyMCE to 4.0.20. Switch from tabbed Visual/HTML
Editor for HTML modules to showing the code editor as a plugin within TinyMCE (triggered
from toolbar). STUD-1422

Studio: Add ability to reorder Pages and hide the Wiki page. STUD-1375

Blades: Added template for iFrames. BLD-611.

Studio: Support for viewing built-in tabs on the Pages page. STUD-1193

Blades: Fixed bug when image mapped input's Show Answer multiplies rectangles on
 many inputtypes. BLD-810.

LMS: Enabled screen reader feedback of problem responses.
  LMS-2158

Blades: Removed tooltip from captions. BLD-629.

Blades: Fix problem with loading YouTube API is it is not available. BLD-531.

Blades: Fix download subs for non youtube videos and non-en language. BLD-897.

Blades: Fix issues related to videos that have separate YouTube IDs for the
different video speeds. BLD-915, BLD-901.

Blades: Add .txt and .srt options to the "download transcript" button. BLD-844.

Blades: Fix bug when transcript cutting off view in full view mode. BLD-852.

Blades: Show start time or starting position on slider and VCR. BLD-823.

Common: Upgraded CodeMirror to 3.21.0 with an accessibility patch applied.
  LMS-1802

Studio: Add new container page that can display nested xblocks. STUD-1244.

Blades: Allow multiple transcripts with video. BLD-642.

CMS: Add feature to allow exporting a course to a git repository by
specifying the giturl in the course settings.

Studio: Fix import/export bug with conditional modules. STUD-149

Blades: Persist student progress in video. BLD-385.

Blades: Fix for the list metadata editor that gets into a bad state where "Add"
  is disabled. BLD-821.

Blades: Add view for field type Dict in Studio. BLD-658.

Blades: Refactor stub implementation of LTI Provider. BLD-601.

LMS: multiple choice features: shuffle, answer-pool, targeted-feedback,
choice name masking, submission timer

Studio: Added ability to edit course short descriptions that appear on the course catalog page.

LMS: In left accordion and progress page, due dates are now displayed in time
zone specified by settings.TIME_ZONE, instead of UTC always

LMS:  If the course start date is kept at the default studio value (Jan 1, 2030)
and advertised_start is not set, the start date is not displayed in the
/courses tile view, the course about page, or the dashboard

LMS: Add ability to redirect to a splash screen.

Blades: Add role parameter to LTI. BLD-583.

Blades: Bugfix "In Firefox YouTube video with start time plays from 00:00:00".
BLD-708.

Blades: Fix bug when image response in Firefox does not retain input. BLD-711.

Blades: Give numerical response tolerance as a range. BLD-25.

Common: Add a utility app for building databased-backed configuration
  for specific application features. Includes admin site customization
  for easier administration and tracking.

Common: Add the ability to dark-launch site translations. These languages
  will be unavailable to users except through the use of a specific query
  parameter.

Blades: Allow user with BetaTester role correctly use LTI. BLD-641.

Blades: Video player persist speed preferences between videos. BLD-237.

Blades: Change the download video field to a dropdown that will allow students
to download the first source listed in the alternate sources. BLD-364.

Blades: Change the track field to a dropdown that will allow students
to download the transcript of the video without timecodes. BLD-368.

Blades: Video player start-end time range is now shown even before Play is
clicked. Video player VCR time shows correct non-zero total time for YouTube
videos even before Play is clicked. BLD-529.

Studio: Add ability to duplicate components on the unit page.

Blades: Adds CookieStorage utility for video player that provides convenient
  way to work with cookies.

Blades: Fix comparison of float numbers. BLD-434.

Blades: Allow regexp strings as the correct answer to a string response question. BLD-475.

Common: MixedModulestore is now the only approved access to the persistence layer
  - takes a new parameter 'reference_type' which can be 'Location' or 'Locator'. Mixed
  then tries to ensure that every reference in any xblock gets converted to that type on
  retrieval. Because we're moving to Locators, the default is Locator; so, you should change
  all existing configurations to 'Location' (unless you're using split)

Common: Add feature flags to allow developer use of pure XBlocks
  - ALLOW_ALL_ADVANCED_COMPONENTS disables the hard-coded list of advanced
    components in Studio, and allows any xblock to be added as an
    advanced component in Studio settings
  - XBLOCK_SELECT_FUNCTION allows the insertion of a custom function
    to limit loading of XBlocks with (including allowing pure xblocks)

Studio: Add sorting by column to the Files & Uploads page.
See mongo_indexes.md for new indices that should be added.

Common: Previously, theming was activated by providing a value for the THEME_NAME
  setting. Now, theming is activated by setting the "USE_CUSTOM_THEME" feature
  flag to True -- a THEME_NAME setting is still required to determine *which*
  theme to use.

Studio: Newly-created courses default to being published on Jan 1, 2030

Studio: Added pagination to the Files & Uploads page.

Common: Centralized authorization mechanisms and removed the app-specific ones.

Blades: Video player improvements:
  - Disable edX controls on iPhone/iPod (native controls are used).
  - Disable unsupported controls (volume, playback rate) on iPad/Android.
  - Controls becomes visible after click on video or play placeholder to avoid
    issues with YouTube API on iPad/Android.
  - Captions becomes visible just after full initialization of video player.
  - Fix blinking of captions after initialization of video player. BLD-206.

LMS: Fix answer distribution download for small courses. LMS-922, LMS-811

Blades: Add template for the zooming image in studio. BLD-206.

Blades: Update behavior of start/end time fields. BLD-506.

Blades: Make LTI module not send grade_back_url if has_score=False. BLD-561.

Blades: Show answer for imageresponse. BLD-21.

Blades: LTI additional Python tests. LTI must use HTTPS for
lis_outcome_service_url. BLD-564.

Studio: Enable Terms of Service and Privacy Policy links to be served by
  an alternate site. STUD-151.

Blades: Fix bug when Image mapping problems are not working for students in IE. BLD-413.

Blades: Add template that displays the most up-to-date features of
drag-and-drop. BLD-479.

Blades: LTI fix bug e-reader error when popping out window. BLD-465.

Common: Switch from mitx.db to edx.db for sqlite databases. This will effectively
  reset state for local instances of the code, unless you manually rename your
  mitx.db file to edx.db.

Common: significant performance improvement for authorization checks and location translations.
  Ensure all auth checks, check all possible permutations of the auth key (Instructor dashboard
  now shows when it should for all courses in lms).
  Made queries for Studio dashboard 2 orders of magnitude faster (and fewer).

Blades: Video Transcripts: Fix clear and download buttons. BLD-438.

Common: Switch over from MITX_FEATURES to just FEATURES. To override items in
  the FEATURES dict, the environment variable you must set to do so is also
  now called FEATURES instead of MITX_FEATURES.

LMS: Change the forum role granted to global staff on enrollment in a
course. Previously, staff were given the Moderator role; now, they are
given the Student role.

Blades: Fix Numerical input to support mathematical operations. BLD-525.

Blades: Improve calculator's tooltip accessibility. Add possibility to navigate
  through the hints via arrow keys. BLD-533.

LMS: Add feature for providing background grade report generation via Celery
  instructor task, with reports uploaded to S3. Feature is visible on the beta
  instructor dashboard. LMS-58

Blades: Added grading support for LTI module. LTI providers can now grade
student's work and send edX scores. OAuth1 based authentication
implemented. BLD-384.

LMS: Beta-tester status is now set on a per-course-run basis, rather than being
  valid across all runs with the same course name. Old group membership will
  still work across runs, but new beta-testers will only be added to a single
  course run.

Blades: Enabled several Video Jasmine tests. BLD-463.

Studio: Continued modification of Studio pages to follow a RESTful framework.
includes Settings pages, edit page for Subsection and Unit, and interfaces
for updating xblocks (xmodules) and getting their editing HTML.

LMS: Improve accessibility of inline discussions in courseware.

Blades: Put 2nd "Hide output" button at top of test box & increase text size for
code response questions. BLD-126.

Blades: Update the calculator hints tooltip with full information. BLD-400.

Blades: Fix transcripts 500 error in studio (BLD-530)

LMS: Add error recovery when a user loads or switches pages in an
inline discussion.

Blades: Allow multiple strings as the correct answer to a string response
question. BLD-474.

Blades: a11y - Videos will alert screenreaders when the video is over.

LMS: Trap focus on the loading element when a user loads more threads
in the forum sidebar to improve accessibility.

LMS: Add error recovery when a user loads more threads in the forum sidebar.

LMS: Add a user-visible alert modal when a forums AJAX request fails.

Blades: Add template for checkboxes response to studio. BLD-193.

Blades: Video player:
  - Add spinner;
  - Improve initialization of modules;
  - Speed up video resizing during page loading;
  - Speed up acceptance tests. (BLD-502)
  - Fix transcripts bug - when show_captions is set to false. BLD-467.

Studio: change create_item, delete_item, and save_item to RESTful API (STUD-847).

Blades: Fix answer choices rearranging if user tries to stylize something in the
text like with bold or italics. (BLD-449)

LMS: Beta instructor dashboard will only count actively enrolled students for
course enrollment numbers.

Blades: Fix speed menu that is not rendered correctly when YouTube is
unavailable. (BLD-457).

LMS: Users with is_staff=True no longer have the STAFF label appear on
their forum posts.

Blades: Video start and end times now function the same for both YouTube and
HTML5 videos. If end time is set, the video can still play until the end, after
it pauses on the end time.

Blades: Disallow users to enter video url's in http.

Studio/LMS: Ability to cap the max number of active enrollments in a course

LMS: Improve the acessibility of the forum follow post buttons.

Blades: Latex problems are now enabled via use_latex_compiler
key in course settings. (BLD-426)

Blades: Fix bug when the speed can only be changed when the video is playing.

LMS: The dialogs on the wiki "changes" page are now accessible to screen
readers.  Now all wiki pages have been made accessible. (LMS-1337)

LMS: Change bulk email implementation to use less memory, and to better handle
duplicate tasks in celery.

LMS: When a topic is selected in the forums navigation sidebar, fetch
the thread list using the /threads endpoint of the comments service
instead of /search/threads, which does not sort and paginate
correctly. This requires at least version 31ef160 of
cs_comments_service.

LMS: Improve forum error handling so that errors in the logs are
clearer and HTTP status codes from the comments service indicating
client error are correctly passed through to the client.

LMS: Improve performance of page load and thread list load for
discussion tab

LMS: The wiki markup cheatsheet dialog is now accessible to screen readers.
(LMS-1303)

Common: Add skip links for accessibility to CMS and LMS. (LMS-1311)

Studio: Change course overview page, checklists, assets, import, export, and course staff
management page URLs to a RESTful interface. Also removed "\listing", which
duplicated "\index".

LMS: Fixed accessibility bug where users could not tab through wiki (LMS-1307)

Blades: When start time and end time are specified for a video, a visual range
will be shown on the time slider to highlight the place in the video that will
be played.

Studio: added restful interface for finding orphans in courses.
An orphan is an xblock to which no children relation points and whose type is not
in the set contentstore.views.item.DETACHED_CATEGORIES nor 'course'.
    GET http://host/orphan/org.course returns json array of ids.
        Requires course author access.
    DELETE http://orphan/org.course deletes all the orphans in that course.
        Requires is_staff access

Studio: Bug fix for text loss in Course Updates when the text exists
before the first tag.

Common: expect_json decorator now puts the parsed json payload into a json attr
on the request instead of overwriting the POST attr

---------- split mongo backend refactoring changelog section ------------

Studio: course catalog, assets, checklists, course outline pages now use course
id syntax w/ restful api style

Common:
  separate the non-sql db connection configuration from the modulestore (xblock modeling) configuration.
  in split, separate the the db connection and atomic crud ops into a distinct module & class from modulestore

Common: location mapper: % encode periods and dollar signs when used as key in the mapping dict

Common: location mapper: added a bunch of new helper functions for generating
old location style info from a CourseLocator

Common: locators: allow - ~ and . in course, branch, and block ids.

---------- end split mongo backend section ---------

Blades: Hovering over CC button in video player, when transcripts are hidden,
will cause them to show up. Moving the mouse from the CC button will auto hide
them. You can hover over the CC button and then move the mouse to the
transcripts which will allow you to select some video position in 1 click.

Blades: Add possibility to use multiple LTI tools per page.

Blades: LTI module can now load external content in a new window.

LMS: Disable data download buttons on the instructor dashboard for large courses

Common: Adds ability to disable a student's account. Students with disabled
accounts will be prohibited from site access.

LMS: Fix issue with CourseMode expiration dates

LMS: Ported bulk emailing to the beta instructor dashboard.

LMS: Add monitoring of bulk email subtasks to display progress on instructor dash.

LMS: Refactor and clean student dashboard templates.

LMS: Fix issue with CourseMode expiration dates

CMS: Add text_customization Dict to advanced settings which can support
string customization at particular spots in the UI.  At first just customizing
the Check/Final Check buttons with keys: custom_check and custom_final_check

LMS: Add PaidCourseRegistration mode, where payment is required before course
registration.

Studio: Switched to loading Javascript using require.js

Studio: Better feedback during the course import process

Studio: Improve drag and drop on the course overview and subsection views.

LMS: Add split testing functionality for internal use.

CMS: Add edit_course_tabs management command, providing a primitive
editing capability for a course's list of tabs.

Studio and LMS: add ability to lock assets (cannot be viewed unless registered
for class).

Studio: add restful interface for paging assets (no UX yet, but just add
/start/45/max/50 to end of url to get items 45-95, e.g.)

LMS: First round of improvements to New (beta) Instructor Dash:
improvements, fixes, and internationalization to the Student Info section.

LMS: Improved accessibility of parts of forum navigation sidebar.

LMS: enhanced accessibility labeling and aria support for the discussion forum
new post dropdown as well as response and comment area labeling.

Blades: Add Studio timed transcripts editor to video player.

LMS: enhanced shib support, including detection of linked shib account
at login page and support for the ?next= GET parameter.

LMS: Experimental feature using the ICE change tracker JS pkg to allow peer
assessors to edit the original submitter's work.

LMS: Fixed a bug that caused links from forum user profile pages to
threads to lead to 404s if the course id contained a '-' character.

Studio/LMS: Add password policy enforcement to new account creation

Studio/LMS: Added ability to set due date formatting through Studio's Advanced
Settings.  The key is due_date_display_format, and the value should be a format
supported by Python's strftime function.

Common: Added configurable backends for tracking events. Tracking events using
the python logging module is the default backend. Support for MongoDB and a
Django database is also available.

Blades: Added Learning Tools Interoperability (LTI) blade. Now LTI components
can be included to courses.

LMS: Added alphabetical sorting of forum categories and subcategories.
It is hidden behind a false defaulted course level flag.

Studio: Allow course authors to set their course image on the schedule
and details page, with support for JPEG and PNG images.

LMS, Studio: Centralized startup code to manage.py and wsgi.py files.
Made studio runnable using wsgi.

Blades: Took videoalpha out of alpha, replacing the old video player

Common: Allow instructors to input complicated expressions as answers to
`NumericalResponse`s. Prior to the change only numbers were allowed, now any
answer from '1/3' to 'sqrt(12)*(1-1/3^2+1/5/3^2)' are valid.

Studio/LMS: Allow for 'preview' and 'published' in a single LMS instance. Use
middlware components to retain the incoming Django request and put in thread
local storage. It is recommended that all developers define a 'preview.localhost'
which maps to the same IP address as localhost in his/her HOSTS file.

LMS: Enable beta instructor dashboard. The beta dashboard is a rearchitecture
of the existing instructor dashboard and is available by clicking a link at
the top right of the existing dashboard.

Common: CourseEnrollment has new fields `is_active` and `mode`. The mode will be
used to differentiate different kinds of enrollments (currently, all enrollments
are honor certificate enrollments). The `is_active` flag will be used to
deactivate enrollments without deleting them, so that we know what course you
*were* enrolled in. Because of the latter change, enrollment and unenrollment
logic has been consolidated into the model -- you should use new class methods
to `enroll()`, `unenroll()`, and to check `is_enrolled()`, instead of creating
CourseEnrollment objects or querying them directly.

LMS: Added bulk email for course feature, with option to optout of individual
course emails.

Studio: Email will be sent to admin address when a user requests course creator
privileges for Studio (edge only).

Studio: Studio course authors (both instructors and staff) will be auto-enrolled
for their courses so that "View Live" works.

Common: Add a new input type ``<formulaequationinput />`` for Formula/Numerical
Responses. It periodically makes AJAX calls to preview and validate the
student's input.

Common: Added ratelimiting to our authentication backend.

Common: Add additional logging to cover login attempts and logouts.

Studio: Send e-mails to new Studio users (on edge only) when their course creator
status has changed. This will not be in use until the course creator table
is enabled.

Studio: Added improvements to Course Creation: richer error messaging, tip
text, and fourth field for course run.

Blades: New features for VideoAlpha player:
1.) Controls are auto hidden after a delay of mouse inactivity - the full video
becomes visible.
2.) When captions (CC) button is pressed, captions stick (not auto hidden after
a delay of mouse inactivity). The video player size does not change - the video
is down-sized and placed in the middle of the black area.
3.) All source code of Video Alpha 2 is written in JavaScript. It is not a basic
conversion from CoffeeScript. The structure of the player has been changed.
4.) A lot of additional unit tests.

LMS: Added user preferences (arbitrary user/key/value tuples, for which
which user/key is unique) and a REST API for reading users and
preferences. Access to the REST API is restricted by use of the
X-Edx-Api-Key HTTP header (which must match settings.EDX_API_KEY; if
the setting is not present, the API is disabled).

LMS: Added endpoints for AJAX requests to enable/disable notifications
(which are not yet implemented) and a one-click unsubscribe page.

Studio: Allow instructors of a course to designate other staff as instructors;
this allows instructors to hand off management of a course to someone else.

Common: Add a manage.py that knows about edx-platform specific settings and
projects

Common: Added *experimental* support for jsinput type.

Studio: Remove XML from HTML5 video component editor. All settings are
moved to be edited as metadata.

Common: Added setting to specify Celery Broker vhost

Common: Utilize new XBlock bulk save API in LMS and CMS.

Studio: Add table for tracking course creator permissions (not yet used).
Update rake django-admin[syncdb] and rake django-admin[migrate] so they
run for both LMS and CMS.

LMS: Added *experimental* crowdsource hinting manager page.

XModule: Added *experimental* crowdsource hinting module.

Studio: Added support for uploading and managing PDF textbooks

Common: Student information is now passed to the tracking log via POST instead
of GET.

Blades: Added functionality and tests for new capa input type:
choicetextresponse.

Common: Add tests for documentation generation to test suite

Blades: User answer now preserved (and changeable) after clicking "show answer"
in choice problems

LMS: Removed press releases

Common: Updated Sass and Bourbon libraries, added Neat library

LMS: Add a MixedModuleStore to aggregate the XMLModuleStore and
MongoMonduleStore

LMS: Users are no longer auto-activated if they click "reset password"
This is now done when they click on the link in the reset password
email they receive (along with usual path through activation email).

LMS: Fixed a reflected XSS problem in the static textbook views.

LMS: Problem rescoring.  Added options on the Grades tab of the
Instructor Dashboard to allow a particular student's submission for a
particular problem to be rescored.  Provides an option to see a
history of background tasks for a given problem and student.

Blades: Small UX fix on capa multiple-choice problems.  Make labels only
as wide as the text to reduce accidental choice selections.

Studio:
- use xblock field defaults to initialize all new instances' fields and
  only use templates as override samples.
- create new instances via in memory create_xmodule and related methods rather
  than cloning a db record.
- have an explicit method for making a draft copy as distinct from making a
  new module.

Studio: Remove XML from the video component editor. All settings are
moved to be edited as metadata.

XModule: Only write out assets files if the contents have changed.

Studio: Course settings are now saved explicitly.

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
typed value, or a String that can be converted to their typed value. For
example, an Integer can contain 3 or '3'. This changed an update to the xblock
library.

LMS: Courses whose id matches a regex in the COURSES_WITH_UNSAFE_CODE Django
setting now run entirely outside the Python sandbox.

Blades: Added tests for Video Alpha player.

Common: Have the capa module handle unicode better (especially errors)

Blades: Video Alpha bug fix for speed changing to 1.0 in Firefox.

Blades: Additional event tracking added to Video Alpha: fullscreen switch,
show/hide captions.

CMS: Allow editors to delete uploaded files/assets

XModules: `XModuleDescriptor.__init__` and `XModule.__init__` dropped the
`location` parameter (and added it as a field), and renamed `system` to
`runtime`, to accord more closely to `XBlock.__init__`

LMS: Some errors handling Non-ASCII data in XML courses have been fixed.

LMS: Add page-load tracking using segment-io (if SEGMENT_IO_LMS_KEY and
SEGMENT_IO_LMS feature flag is on)

Blades: Simplify calc.py (which is used for the Numerical/Formula responses);
add trig/other functions.

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

Common: all dates and times are not time zone aware datetimes. No code should
create or use struct_times nor naive datetimes.

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

Studio: Add feedback to end user if there is a problem exporting a course

Studio: Improve link re-writing on imports into a different course-id

Studio: Allow for intracourse linking in Capa Problems

Blades: Videoalpha.

XModules: Added partial credit for foldit module.

XModules: Added "randomize" XModule to list of XModule types.

XModules: Show errors with full descriptors.

Studio: Add feedback to end user if there is a problem exporting a course

Studio: Improve link re-writing on imports into a different course-id

XQueue: Fixed (hopefully) worker crash when the connection to RabbitMQ is
dropped suddenly.

XQueue: Upload file submissions to a specially named bucket in S3.

Common: Removed request debugger.

Common: Updated Django to version 1.4.5.

Common: Updated CodeJail.

Common: Allow setting of authentication session cookie name.

LMS: Option to email students when enroll/un-enroll them.

Blades: Added WAI-ARIA markup to the video player controls. These are now fully
accessible by screen readers.

Common: Added advanced_module for annotating images to go with the ones for text and videos.
