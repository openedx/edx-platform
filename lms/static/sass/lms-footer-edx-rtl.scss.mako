// Footer for edx.org (right-to-left)
// ==================================

// libs and resets *do not edit*
@import 'bourbon/bourbon'; // lib - bourbon
@import 'vendor/bi-app/bi-app-rtl'; // set the layout for right to left languages

// base - utilities
@import 'base/variables';
@import 'base/mixins';

footer#footer-edx-v3 {
    @import 'base/extends';

    // base - starter
    @import 'base/base';
}

// base - elements
@import 'elements/typography';

// shared - platform
@import 'shared/footer-edx';
