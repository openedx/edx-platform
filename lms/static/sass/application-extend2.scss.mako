## NOTE: This Sass infrastructure is redundant, but needed in order to address an IE9 rule limit within CSS - http://blogs.msdn.com/b/ieinternals/archive/2011/05/14/10164546.aspx

// lms - css application architecture (platform)
// ====================

// libs and resets *do not edit*
@import 'bourbon/bourbon'; // lib - bourbon
@import 'vendor/bi-app/bi-app-ltr'; // set the layout for left to right languages


// BASE  *default edX offerings*
// ====================

// base - utilities
@import 'base/reset';
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
@import 'base/font_face';
@import 'base/extends';
@import 'base/animations';

// base - starter
@import 'base/base';

// base - elements
@import 'elements/typography';
@import 'elements/controls';
@import 'elements/system-feedback';

// base - specific views
@import "views/account-settings";
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

// temp - shame and developer
@import 'developer'; // used for any developer-created scss that needs further polish/refactoring
@import 'shame';     // used for any bad-form/orphaned scss
## NOTE: needed here for cascade and dependency purposes, but not a great permanent solution
