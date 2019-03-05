/* globals gettext */

import Backbone from 'backbone';

import HtmlUtils from 'edx-ui-toolkit/js/utils/html-utils';

class EntitlementUnenrollmentView extends Backbone.View {
  constructor(options) {
    const defaults = {
      el: '.js-entitlement-unenrollment-modal',
    };
    super(Object.assign({}, defaults, options));
  }

  initialize(options) {
    const view = this;

    this.closeButtonSelector = '.js-entitlement-unenrollment-modal .js-entitlement-unenrollment-modal-close-btn';
    this.headerTextSelector = '.js-entitlement-unenrollment-modal .js-entitlement-unenrollment-modal-header-text';
    this.errorTextSelector = '.js-entitlement-unenrollment-modal .js-entitlement-unenrollment-modal-error-text';
    this.submitButtonSelector = '.js-entitlement-unenrollment-modal .js-entitlement-unenrollment-modal-submit';
    this.triggerSelector = '.js-entitlement-action-unenroll';
    this.mainPageSelector = '#dashboard-main';
    this.genericErrorMsg = gettext('Your unenrollment request could not be processed. Please try again later.');
    this.modalId = `#${this.$el.attr('id')}`;

    this.dashboardPath = options.dashboardPath;
    this.signInPath = options.signInPath;
    this.browseCourses = options.browseCourses;
    this.isEdx = options.isEdx;

    this.$submitButton = $(this.submitButtonSelector);
    this.$closeButton = $(this.closeButtonSelector);
    this.$headerText = $(this.headerTextSelector);
    this.$errorText = $(this.errorTextSelector);

    this.$submitButton.on('click', this.handleSubmit.bind(this));

    $(this.triggerSelector).each(function setUpTrigger() {
      const $trigger = $(this);

      $trigger.on('click', view.handleTrigger.bind(view));

      // From accessibility_tools.js
      if (window.accessible_modal) {
        window.accessible_modal(
          `#${$trigger.attr('id')}`,
          view.closeButtonSelector,
          `#${view.$el.attr('id')}`,
          view.mainPageSelector,
        );
      }
    });
  }

  handleTrigger(event) {
    const $trigger = $(event.target);
    const courseName = $trigger.data('courseName');
    const courseNumber = $trigger.data('courseNumber');
    const apiEndpoint = $trigger.data('entitlementApiEndpoint');

    this.$previouslyFocusedElement = $trigger;

    this.resetModal();
    this.setHeaderText(courseName, courseNumber);
    this.setSubmitData(apiEndpoint);
    this.$el.css('position', 'fixed');
  }

  handleSubmit() {
    const apiEndpoint = this.$submitButton.data('entitlementApiEndpoint');

    if (apiEndpoint === undefined) {
      this.setError(this.genericErrorMsg);
      return;
    }

    this.$submitButton.prop('disabled', true);
    $.ajax({
      url: apiEndpoint,
      method: 'DELETE',
      complete: this.onComplete.bind(this),
    });
  }

  resetModal() {
    this.$submitButton.removeData();
    this.$submitButton.prop('disabled', false);
    this.$headerText.empty();
    this.$errorText.removeClass('entitlement-unenrollment-modal-error-text-visible');
    this.$errorText.empty();
  }

  setError(message) {
    this.$submitButton.prop('disabled', true);
    this.$errorText.empty();
    HtmlUtils.setHtml(
                        this.$errorText,
                        message,
                    );
    this.$errorText.addClass('entitlement-unenrollment-modal-error-text-visible');
  }

  setHeaderText(courseName, courseNumber) {
    this.$headerText.empty();
    HtmlUtils.setHtml(
      this.$headerText,
      HtmlUtils.interpolateHtml(
        gettext('Are you sure you want to unenroll from {courseName} ({courseNumber})? You will be refunded the amount you paid.'), // eslint-disable-line max-len
        {
          courseName,
          courseNumber,
        },
      ),
    );
  }

  setSubmitData(apiEndpoint) {
    this.$submitButton.removeData();
    this.$submitButton.data('entitlementApiEndpoint', apiEndpoint);
  }

  switchToSlideOne() {
    this.$('.entitlement-unenrollment-modal-inner-wrapper header').addClass('hidden');
    this.$('.entitlement-unenrollment-modal-submit-wrapper').addClass('hidden');
    this.$('.slide1').removeClass('hidden');
    this.$('.entitlement-unenrollment-modal-inner-wrapper').prevObject.addClass('entitlement-unenrollment-modal-long-survey');

    // From accessibility_tools.js
    window.trapFocusForAccessibleModal(
      this.$previouslyFocusedElement,
      window.focusableElementsString,
      this.closeButtonSelector,
      this.modalId,
      this.mainPageSelector,
    );
  }

  switchToSlideTwo() {
    const price = this.$(".reasons_survey input[name='priceEntitlementUnenrollment']:checked").val();
    const dissastisfied = this.$(".reasons_survey input[name='dissastisfiedEntitlementUnenrollment']:checked").val();
    const difficult = this.$(".reasons_survey input[name='difficultEntitlementUnenrollment']:checked").val();
    const time = this.$(".reasons_survey input[name='timeEntitlementUnenrollment']:checked").val();
    const unavailable = this.$(".reasons_survey input[name='unavailableEntitlementUnenrollment']:checked").val();
    const email = this.$(".reasons_survey input[name='emailEntitlementUnenrollment']:checked").val();

    if (price || dissastisfied || difficult || time || unavailable || email) {
      const results = { price, dissastisfied, difficult, time, unavailable, email };

      window.analytics.track('entitlement_unenrollment_reason.selected', {
        category: 'user-engagement',
        label: JSON.stringify(results),
        displayName: 'v1',
      });
    }
    this.$('.slide1').addClass('hidden');
    this.$('.slide2').removeClass('hidden');
    this.$('.entitlement-unenrollment-modal-inner-wrapper').prevObject.removeClass('entitlement-unenrollment-modal-long-survey');

    // From accessibility_tools.js
    window.trapFocusForAccessibleModal(
      this.$previouslyFocusedElement,
      window.focusableElementsString,
      this.closeButtonSelector,
      this.modalId,
      this.mainPageSelector,
    );
  }

  onComplete(xhr) {
    const status = xhr.status;
    const message = xhr.responseJSON && xhr.responseJSON.detail;

    if (status === 204) {
      if (this.isEdx) {
        this.switchToSlideOne();
        this.$('.reasons_survey:first .submit-reasons').click(this.switchToSlideTwo.bind(this));
      } else {
        EntitlementUnenrollmentView.redirectTo(this.dashboardPath);
      }
    } else if (status === 401 && message === 'Authentication credentials were not provided.') {
      EntitlementUnenrollmentView.redirectTo(`${this.signInPath}?next=${encodeURIComponent(this.dashboardPath)}`);
    } else {
      this.setError(this.genericErrorMsg);
    }
  }

  static redirectTo(path) {
    window.location.href = path;
  }
}

export default EntitlementUnenrollmentView;
