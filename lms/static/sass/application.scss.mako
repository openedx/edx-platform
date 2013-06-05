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

// Multicourse styles
@import 'shared/forms';
@import 'shared/footer';
@import 'shared/header';
@import 'shared/course_object';
@import 'shared/course_filter';
@import 'shared/modal';
@import 'shared/activation_messages';

@import 'multicourse/home';
@import 'multicourse/dashboard';
@import 'multicourse/account';
@import 'multicourse/testcenter-register';
@import 'multicourse/courses';
@import 'multicourse/course_about';
@import 'multicourse/jobs';
@import 'multicourse/media-kit';
@import 'multicourse/about_pages';
@import 'multicourse/press_release';
@import 'multicourse/password_reset';
@import 'multicourse/error-pages';
@import 'multicourse/help';
@import 'multicourse/edge';

@import 'discussion';
@import 'news';

@import 'shame';
