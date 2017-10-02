/* globals gettext, Logger */

export class CourseHome {  // eslint-disable-line import/prefer-default-export
  constructor(options) {
    this.courseRunKey = options.courseRunKey;
    this.msgStateStorageKey = `course_experience.upgrade_msg.${this.courseRunKey}.collapsed`;

    // Logging for 'Resume Course' or 'Start Course' button click
    const $resumeCourseLink = $(options.resumeCourseLink);
    $resumeCourseLink.on('click', (event) => {
      const eventType = $resumeCourseLink.find('span').data('action-type');
      Logger.log(
        'edx.course.home.resume_course.clicked',
        {
          event_type: eventType,
          url: event.currentTarget.href,
        },
      );
    });

    // Logging for course tool click events
    const $courseToolLink = $(options.courseToolLink);
    $courseToolLink.on('click', (event) => {
      const courseToolName = event.srcElement.dataset['analytics-id']; // eslint-disable-line dot-notation
      Logger.log(
        'edx.course.tool.accessed',
        {
          tool_name: courseToolName,
        },
      );
    });

    // Dismissibility for in course messages
    $(document.body).on('click', '.course-message .dismiss', (event) => {
      $(event.target).closest('.course-message').hide();
    });

    // Allow dismiss on enter press for accessibility purposes
    $(document.body).on('keyup', '.course-message .dismiss', (event) => {
      if (event.which === 13) {
        $(event.target).trigger('click');
      }
    });

    $(document).ready(() => {
      this.configureUpgradeMessage();
    });
  }

  static fireSegmentEvent(event, properties) {
    /* istanbul ignore next */
    if (!window.analytics) {
      return;
    }

    window.analytics.track(event, properties);
  }

  /**
   * Persists the collapsed state of the upgrade message. If the message is collapsed,
   * this information is persisted to local storage. Expanding the message *removes* the
   * key from local storage.
   */
  persistUpgradeMessageState(collapsed) {
    if (window.localStorage) {
      if (collapsed) {
        window.localStorage.setItem(this.msgStateStorageKey, true);
      } else {
        window.localStorage.removeItem(this.msgStateStorageKey);
      }
    }
  }

  configureUpgradeMessage() {
    const $vcMessage = $('.vc-message');
    const $vcDismissToggle = $('.vc-toggle', $vcMessage);
    const logEventProperties = { courseRunKey: this.courseRunKey };
    const promotionEventProperties = {
      promotion_id: 'courseware_verified_certificate_upsell',
      creative: 'hero_matthew_smith',
      name: 'In-Course Verification Prompt',
      position: 'hero',
    };

    CourseHome.fireSegmentEvent('Promotion Viewed', promotionEventProperties);
    Logger.log('edx.course.upgrade.hero.displayed', logEventProperties);

    // Get height of container and button
    let vcHeight = $vcMessage.outerHeight();

    // Update based on window
    window.onresize = () => {
      if (!$vcMessage.hasClass('polite')) {
        vcHeight = $vcMessage.outerHeight();
      }
    };

    function collapseMessage(duration = 400) {
      $('.vc-fade').fadeOut(duration, () => {
        $vcDismissToggle.text(gettext('Show more')).attr('aria-expanded', false);
        $('.vc-polite-only').fadeIn(duration);
        $vcMessage.height('auto').addClass('polite');
      });
    }

    // Use the previously-persisted state to determine the initial display state of the message.
    if (window.localStorage && window.localStorage.getItem(this.msgStateStorageKey)) {
      collapseMessage(0);
    }
    $vcMessage.show();

    $vcDismissToggle.click(() => {
      if ($vcMessage.hasClass('polite')) {
        // Expand message
        Logger.log('edx.course.upgrade.hero.expanded', logEventProperties);
        this.persistUpgradeMessageState(false);

        $('.vc-fade').fadeOut(400);
        $vcMessage.animate({ height: vcHeight }, 400, () => {
          $vcMessage.height('auto').removeClass('polite');
          $vcDismissToggle.text(gettext('Show less')).attr('aria-expanded', true);
          $('.vc-fade').fadeIn(400);
        });
      } else {
        // Collapse message
        Logger.log('edx.course.upgrade.hero.collapsed', logEventProperties);
        this.persistUpgradeMessageState(true);
        collapseMessage();
      }
    });

    $('.btn-upgrade', $vcMessage).click(() => {
      CourseHome.fireSegmentEvent('Promotion Clicked', promotionEventProperties);
      Logger.log('edx.course.upgrade.hero.clicked', logEventProperties);
    });
  }
}
