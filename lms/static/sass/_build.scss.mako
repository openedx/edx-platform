## Note: This Sass infrastructure is repeated in application-extend1 and application-extend2, but needed in order to address an IE9 rule limit within CSS - http://blogs.msdn.com/b/ieinternals/archive/2011/05/14/10164546.aspx

// lms - css application architecture
// ====================

// BASE  *default edX offerings*
// ====================

// base - utilities
@import 'base/reset';
@import 'base/font_face';
@import 'base/variables';
@import 'base/mixins';

## THEMING
## -------
## Set up this file to import an edX theme library if the environment
## indicates that a theme should be used. The assumption is that the
## theme resides outside of this main edX repository, in a directory
## called themes/<theme-name>/, with its base Sass file in
## themes/<theme-name>/static/sass/_<theme-name>.scss. That one entry
## point can be used to @import in as many other things as needed.
% if env["FEATURES"].get("USE_CUSTOM_THEME", False):
  // import theme's Sass overrides
  @import '${env.get('THEME_NAME')}';
% endif

@import 'base/base';

// base - assets
@import 'base/extends';
@import 'base/animations';

// base - starter
@import 'base/base';

// base - elements
@import 'elements/typography';
@import 'elements/controls';
@import 'elements/system-feedback';
@import 'elements/navigation'; // all archetypes of navigation

// shared - course
@import 'shared/forms';
@import 'shared/footer';
@import 'shared/header';
@import 'shared/course_object';
@import 'shared/course_filter';
@import 'shared/modal';
@import 'shared/activation_messages';
@import 'shared/unsubscribe';
@import 'shared/tooltips';

// shared - platform
@import 'multicourse/home';
@import 'multicourse/dashboard';
@import 'multicourse/account';
@import 'multicourse/courses';
@import 'multicourse/course_about';
@import 'multicourse/jobs';
@import 'multicourse/media-kit';
@import 'multicourse/about_pages';
@import 'multicourse/press_release';
@import 'multicourse/error-pages';
@import 'multicourse/help';
@import 'multicourse/edge';
@import 'multicourse/survey-page';

// base - specific views
@import 'views/login-register';
@import 'views/verification';
@import 'views/decoupled-verification';
@import 'views/shoppingcart';

// applications
@import "discussion/utilities/variables";
@import "discussion/mixins";
@import 'discussion/discussion'; // Process old file after definitions but before everything else
@import "discussion/elements/actions";
@import "discussion/elements/editor";
@import "discussion/elements/labels";
@import "discussion/elements/navigation";
@import "discussion/views/thread";
@import "discussion/views/create-edit-post";
@import "discussion/views/response";
@import 'discussion/utilities/developer';
@import 'discussion/utilities/shame';

@import 'news';

@import 'developer'; // used for any developer-created scss that needs further polish/refactoring
@import 'shame';     // used for any bad-form/orphaned scss

// course - base
@import 'course/layout/courseware_header';
@import 'course/layout/courseware_preview';
@import 'course/layout/footer';
@import 'course/base/mixins';
@import 'course/base/base';
@import 'course/base/extends';
@import '../../../common/static/xmodule/modules/css/module-styles.scss';
@import 'course/courseware/courseware';
@import 'course/courseware/sidebar';
@import 'course/courseware/amplifier';

## Import styles for courseware search
% if env["FEATURES"].get("ENABLE_COURSEWARE_SEARCH"):
    @import 'course/courseware/courseware_search';
% endif

// course - modules
@import 'course/modules/student-notes'; // student notes
@import 'course/modules/calculator'; // calculator utility
@import 'course/modules/timer'; // timer
@import 'course/modules/chat'; // chat utility


// course - specific courses
@import "course/courseware/courses/_cs188.scss";

// course - wiki
@import "course/wiki/basic-html";
@import "course/wiki/sidebar";
@import "course/wiki/create";
@import "course/wiki/wiki";
@import "course/wiki/table";

// course - views
@import "course/info";
@import "course/syllabus"; // TODO arjun replace w/ custom tabs, see courseware/courses.py
@import "course/textbook";
@import "course/profile";
@import "course/gradebook";
@import "course/tabs";
@import "course/staff_grading";
@import "course/rubric";
@import "course/open_ended_grading";
@import "course/student-notes";

// course - instructor-only views
@import "course/instructor/instructor";
@import "course/instructor/instructor_2";
@import "course/instructor/email";
@import "../../../common/static/xmodule/descriptors/css/module-styles.scss";

// course - discussion
@import "course/discussion/form-wmd-toolbar";

// IE fixes
@import "ie";
