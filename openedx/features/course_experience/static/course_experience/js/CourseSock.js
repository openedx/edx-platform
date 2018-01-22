/* globals Logger */

export class CourseSock {  // eslint-disable-line import/prefer-default-export
  constructor() {
    const $toggleActionButton = $('.action-toggle-verification-sock');
    const $verificationSock = $('.verification-sock .verification-main-panel');
    const $upgradeToVerifiedButton = $('.verification-sock .action-upgrade-certificate');
    const $miniCert = $('.mini-cert');
    const pageLocation = window.location.href.indexOf('courseware') > -1
        ? 'Course Content Page' : 'Home Page';

    // Behavior to fix button to bottom of screen on scroll
    const fixUpgradeButton = () => {
      if (!$upgradeToVerifiedButton.is(':visible')) return;

      // Grab the current scroll location
      const documentBottom = $(window).scrollTop() + $(window).height();

      // Establish a sliding window in which the button is fixed
      const startFixed = $verificationSock.offset().top + 320;
      const endFixed = (startFixed + $verificationSock.height()) - 220;

      // Ensure update button stays in sock even when max-width is exceeded
      const distRight = window.outerWidth - ($miniCert.offset().left + $miniCert.width());

      // Update positioning when scrolling is in fixed window and screen width is sufficient
      if ((documentBottom > startFixed && documentBottom < endFixed
          && $(window).width() > 960)) {
        $upgradeToVerifiedButton.addClass('attached');
        $upgradeToVerifiedButton.css('right', `${distRight}px`);
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
    $toggleActionButton.on('click', () => {
      const toggleSpeed = 400;
      $toggleActionButton.toggleClass('active');
      $verificationSock.slideToggle(toggleSpeed, fixUpgradeButton);

      // Toggle aria-expanded attribute
      const newAriaExpandedState = $toggleActionButton.attr('aria-expanded') === 'false';
      $toggleActionButton.attr('aria-expanded', newAriaExpandedState);

      // Log open and close events
      const isOpening = $toggleActionButton.hasClass('active');
      const logMessage = isOpening ? 'edx.bi.course.sock.toggle_opened'
          : 'edx.bi.course.sock.toggle_closed';
      window.analytics.track(
        logMessage,
        {
          from_page: pageLocation,
        },
      );
    });

    $upgradeToVerifiedButton.on('click', () => {
      Logger.log(
        'edx.course.enrollment.upgrade.clicked',
        {
          location: 'sock',
        },
      );
    });
  }
}
