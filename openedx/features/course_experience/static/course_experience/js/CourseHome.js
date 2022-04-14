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

    // Course goal editing elements
    const $goalSection = $('.section-goals');
    const $editGoalIcon = $('.section-goals .edit-icon');
    const $currentGoalText = $('.section-goals .goal');
    const $goalSelect = $('.section-goals .edit-goal-select');
    const $responseIndicator = $('.section-goals .response-icon');
    const $responseMessageSr = $('.section-goals .sr-update-response-msg');
    const $goalUpdateTitle = $('.section-goals .title:not("label")');
    const $goalUpdateLabel = $('.section-goals label.title');

    // Switch to editing mode when the goal section is clicked
    $goalSection.on('click', (event) => {
      if (!$(event.target).hasClass('edit-goal-select')) {
        $goalSelect.toggle();
        $currentGoalText.toggle();
        $goalUpdateTitle.toggle();
        $goalUpdateLabel.toggle();
        $responseIndicator.removeClass().addClass('response-icon');
        $goalSelect.focus();
      }
    });

    // Trigger click event on enter press for accessibility purposes
    $(document.body).on('keyup', '.section-goals .edit-icon', (event) => {
      if (event.which === 13) {
        $(event.target).trigger('click');
      }
    });

    // Send an ajax request to update the course goal
    $goalSelect.on('blur change', (event) => {
      $currentGoalText.show();
      $goalUpdateTitle.show();
      $goalUpdateLabel.hide();
      $goalSelect.hide();
      // No need to update in the case of a blur event
      if (event.type === 'blur') return;
      const newGoalKey = $(event.target).val();
      $responseIndicator.removeClass().addClass('response-icon fa fa-spinner fa-spin');
      $.ajax({
        method: 'POST',
        url: options.goalApiUrl,
        headers: { 'X-CSRFToken': $.cookie('csrftoken') },
        data: {
          goal_key: newGoalKey,
          course_key: options.courseId,
          user: options.username,
        },
        dataType: 'json',
        success: (data) => {
          $currentGoalText.find('.text').text(data.goal_text);
          $responseMessageSr.text(gettext('You have successfully updated your goal.'));
          $responseIndicator.removeClass().addClass('response-icon fa fa-check');
        },
        error: () => {
          $responseIndicator.removeClass().addClass('response-icon fa fa-close');
          $responseMessageSr.text(gettext('There was an error updating your goal.'));
        },
        complete: () => {
          // Only show response icon indicator for 3 seconds.
          setTimeout(() => {
            $responseIndicator.removeClass().addClass('response-icon');
          }, 3000);
          $editGoalIcon.focus();
        },
      });
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
      this.configureUpgradeAnalytics();
    });
  }

  static fireSegmentEvent(event, properties) {
    /* istanbul ignore next */
    if (!window.analytics) {
      return;
    }

    window.analytics.track(event, properties);
  }

  // Promotion analytics for upgrade messages on course home.
  // eslint-disable-next-line class-methods-use-this
  configureUpgradeAnalytics() {
    $('.btn-upgrade').each(
      (index, button) => {
        const promotionEventProperties = {
          promotion_id: 'courseware_verified_certificate_upsell',
          creative: $(button).data('creative'),
          name: 'In-Course Verification Prompt',
          position: $(button).data('position'),
        };
        CourseHome.fireSegmentEvent('Promotion Viewed', promotionEventProperties);
        $(button).click(() => {
          CourseHome.fireSegmentEvent('Promotion Clicked', promotionEventProperties);
        });
      },
    );
  }

  configureUpgradeMessage() {
    const logEventProperties = { courseRunKey: this.courseRunKey };

    Logger.log('edx.bi.course.upgrade.sidebarupsell.displayed', logEventProperties);
    $('.section-upgrade .btn-upgrade').click(() => {
      Logger.log('edx.bi.course.upgrade.sidebarupsell.clicked', logEventProperties);
      Logger.log('edx.course.enrollment.upgrade.clicked', { location: 'sidebar-message' });
    });
    $('.promo-learn-more').click(() => {
      $('.action-toggle-verification-sock').click();
      $('.action-toggle-verification-sock')[0].scrollIntoView({ behavior: 'smooth', alignToTop: true });
    });
  }
}
