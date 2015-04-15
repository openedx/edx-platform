@import 'bourbon/bourbon';
@import 'vendor/bi-app/bi-app-ltr'; // set the layout for left to right languages

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
@import 'base/extends';
@import 'base/animations';
@import 'shared/tooltips';

// base - elements
@import 'elements/typography';
@import 'elements/controls';
@import 'elements/navigation'; // all archetypes of navigation

// course - base
@import 'course/layout/courseware_header';
@import 'course/layout/courseware_preview';
@import 'course/layout/footer';
@import 'course/base/mixins';
@import 'course/base/base';
@import 'course/base/extends';
@import 'xmodule/modules/css/module-styles.scss';
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
@import "xmodule/descriptors/css/module-styles.scss";

// course - ccx_coach
@import "course/ccx_coach/dashboard";

// discussion
@import "course/discussion/form-wmd-toolbar";
