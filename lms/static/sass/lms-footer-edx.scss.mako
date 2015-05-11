// Footer for edx.org (left-to-right)
// ==================================

// libs and resets *do not edit*
@import 'bourbon/bourbon'; // lib - bourbon
@import 'vendor/bi-app/bi-app-ltr'; // set the layout for left to right languages

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
