/* globals gettext */

import Backbone from 'backbone';

class UnenrollView extends Backbone.View {

  constructor(options) {
    const defaults = {
      el: '.unenroll-modal',
    };
    super(Object.assign({}, defaults, options));
  }

  switchToSlideOne() {
    // Randomize survey option order
    const survey = document.querySelector('.options');
    for (let i = survey.children.length - 1; i >= 0; i -= 1) {
      survey.appendChild(survey.children[Math.trunc(Math.random() * i)]);
    }
    this.$('.inner-wrapper header').hide();
    this.$('#unenroll_form').hide();
    this.$('.slide1').removeClass('hidden');
  }

  switchToSlideTwo() {
    let reason = this.$(".reasons_survey input[name='reason']:checked").attr('val');
    if (reason === 'Other') {
      reason = this.$('.other_text').val();
    }
    if (reason) {
      window.analytics.track('unenrollment_reason.selected', {
        category: 'user-engagement',
        label: reason,
        displayName: 'v1',
      });
    }
    this.$('.slide1').addClass('hidden');
    this.$('.survey_course_name').text(this.$('#unenroll_course_name').text());
    this.$('.slide2').removeClass('hidden');
    this.$('.reasons_survey .return_to_dashboard').attr('href', this.urls.dashboard);
    this.$('.reasons_survey .browse_courses').attr('href', this.urls.browseCourses);
  }

  unenrollComplete(event, xhr) {
    if (xhr.status === 200) {
      if (!this.isEdx) {
        location.href = this.urls.dashboard;
      } else {
        this.switchToSlideOne();
        this.$('.reasons_survey:first .submit_reasons').click(this.switchToSlideTwo.bind(this));
      }
    } else if (xhr.status === 403) {
      location.href = `${this.urls.signInUser}?course_id=${
        encodeURIComponent($('#unenroll_course_id').val())}&enrollment_action=unenroll`;
    } else {
      $('#unenroll_error').text(
        gettext('Unable to determine whether we should give you a refund because' +
                ' of System Error. Please try again later.'),
      ).stop()
       .css('display', 'block');
    }
  }

  initialize(options) {
    this.urls = options.urls;
    this.isEdx = options.isEdx;

    $('#unenroll_form').on('ajax:complete', this.unenrollComplete.bind(this));
  }
}

export default UnenrollView;
