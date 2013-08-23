// lms - css application architecture
// ====================

// libs and resets *do not edit*
@import 'bourbon/bourbon'; // lib - bourbon

// VENDOR + REBASE *referenced/used vendor presentation and reset*
// ====================

@import 'base/reset';
@import 'vendor/font-awesome';


// BASE  *default edX offerings*
// ====================
// base - utilities

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

// base - assets
@import 'base/font_face';
@import 'base/extends';
@import 'base/animations'; 	

// base - starter
@import 'base/base';

// shared - course 
@import 'shared/forms';
@import 'shared/footer';
@import 'shared/header';
@import 'shared/course_object';
@import 'shared/course_filter';
@import 'shared/modal';
@import 'shared/activation_messages';
@import 'shared/unsubscribe';

// shared - platform
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

// applications 
@import 'discussion';
@import 'news';

@import 'shame'; // shame file - used for any bad-form/orphaned scss that knowingly violate edX FED architecture/standards (see - http://csswizardry.com/2013/04/shame-css/)
