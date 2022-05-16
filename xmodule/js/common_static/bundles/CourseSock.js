(function(e, a) { for(var i in a) e[i] = a[i]; }(window, webpackJsonp([63],{

/***/ "./openedx/features/course_experience/static/course_experience/js/CourseSock.js":
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
Object.defineProperty(__webpack_exports__, "__esModule", { value: true });
/* WEBPACK VAR INJECTION */(function($) {/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "CourseSock", function() { return CourseSock; });
function _classCallCheck(instance, Constructor) { if (!(instance instanceof Constructor)) { throw new TypeError("Cannot call a class as a function"); } }

/* globals Logger */

var CourseSock = // eslint-disable-line import/prefer-default-export
function CourseSock() {
  _classCallCheck(this, CourseSock);

  var $toggleActionButton = $('.action-toggle-verification-sock');
  var $verificationSock = $('.verification-sock .verification-main-panel');
  var $upgradeToVerifiedButton = $('.verification-sock .action-upgrade-certificate');
  var $miniCert = $('.mini-cert');
  var pageLocation = window.location.href.indexOf('courseware') > -1 ? 'Course Content Page' : 'Home Page';

  // Behavior to fix button to bottom of screen on scroll
  var fixUpgradeButton = function fixUpgradeButton() {
    if (!$upgradeToVerifiedButton.is(':visible')) return;

    // Grab the current scroll location
    var documentBottom = $(window).scrollTop() + $(window).height();

    // Establish a sliding window in which the button is fixed
    var startFixed = $verificationSock.offset().top + 320;
    var endFixed = startFixed + $verificationSock.height() - 220;

    // Ensure update button stays in sock even when max-width is exceeded
    var distRight = window.outerWidth - ($miniCert.offset().left + $miniCert.width());

    // Update positioning when scrolling is in fixed window and screen width is sufficient
    if (documentBottom > startFixed && documentBottom < endFixed && $(window).width() > 960) {
      $upgradeToVerifiedButton.addClass('attached');
      $upgradeToVerifiedButton.css('right', distRight + 'px');
    } else {
      // If outside sliding window, reset to un-attached state
      $upgradeToVerifiedButton.removeClass('attached');
      $upgradeToVerifiedButton.css('right', '20px');

      // Add class to define absolute location
      if (documentBottom < startFixed) {
        $upgradeToVerifiedButton.addClass('stuck-top');
        $upgradeToVerifiedButton.removeClass('stuck-bottom');
      } else if (documentBottom > endFixed) {
        $upgradeToVerifiedButton.addClass('stuck-bottom');
        $upgradeToVerifiedButton.removeClass('stuck-top');
      }
    }
  };

  // Fix the sock to the screen on scroll and resize events
  if ($upgradeToVerifiedButton.length) {
    $(window).scroll(fixUpgradeButton).resize(fixUpgradeButton);
  }

  // Open the sock when user clicks to Learn More
  $toggleActionButton.on('click', function () {
    var toggleSpeed = 400;
    $toggleActionButton.toggleClass('active');
    $verificationSock.slideToggle(toggleSpeed, fixUpgradeButton);

    // Toggle aria-expanded attribute
    var newAriaExpandedState = $toggleActionButton.attr('aria-expanded') === 'false';
    $toggleActionButton.attr('aria-expanded', newAriaExpandedState);

    // Log open and close events
    var isOpening = $toggleActionButton.hasClass('active');
    var logMessage = isOpening ? 'edx.bi.course.sock.toggle_opened' : 'edx.bi.course.sock.toggle_closed';
    window.analytics.track(logMessage, {
      from_page: pageLocation
    });
  });

  $upgradeToVerifiedButton.on('click', function () {
    Logger.log('edx.course.enrollment.upgrade.clicked', {
      location: 'sock'
    });
  });
};
/* WEBPACK VAR INJECTION */}.call(__webpack_exports__, __webpack_require__(0)))

/***/ })

},["./openedx/features/course_experience/static/course_experience/js/CourseSock.js"])));
//# sourceMappingURL=CourseSock.js.map