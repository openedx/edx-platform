@import 'bourbon/bourbon';

@import 'base/reset';
@import 'base/font_face';
@import 'base/mixins';
@import 'base/variables';

## THEMING
## -------
## Set up this file to import an edX theme library if the environment
## indicates that a theme should be used. The assumption is that the
## theme resides outside of this main edX repository, in a directory
## called themes/<theme-name>/, with its base Sass file in
## themes/<theme-name>/static/sass/_<theme-name>.scss. That one entry
## point can be used to @import in as many other things as needed.
% if env.get('THEME_NAME') is not None:
  // import theme's Sass overrides
  @import '${env.get('THEME_NAME')}';
% endif

@import 'base/base';
@import 'base/extends';
@import 'base/animations';
@import 'shared/tooltips';

// Course base / layout styles
@import 'course/layout/courseware_header';
@import 'course/layout/footer';
@import 'course/base/mixins';
@import 'course/base/base';
@import 'course/base/extends';
@import 'xmodule/modules/css/module-styles.scss';

// courseware
@import 'course/courseware/courseware';
@import 'course/courseware/sidebar';
@import 'course/courseware/amplifier';
@import 'course/layout/calculator';
@import 'course/layout/timer';
@import 'course/layout/chat';

// course-specific courseware (all styles in these files should be gated by a
// course-specific class). This should be replaced with a better way of
// providing course-specific styling.
@import "course/courseware/courses/_cs188.scss";

// wiki
@import "course/wiki/basic-html";
@import "course/wiki/sidebar";
@import "course/wiki/create";
@import "course/wiki/wiki";
@import "course/wiki/table";

// pages
@import "course/info";
@import "course/syllabus"; // TODO arjun replace w/ custom tabs, see courseware/courses.py
@import "course/textbook";
@import "course/profile";
@import "course/gradebook";
@import "course/tabs";
@import "course/staff_grading";
@import "course/rubric";
@import "course/open_ended_grading";

// instructor
@import "course/instructor/instructor";
@import "course/instructor/instructor_2";

// discussion
@import "course/discussion/form-wmd-toolbar";
