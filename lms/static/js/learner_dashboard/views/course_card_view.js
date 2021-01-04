import Backbone from 'backbone';

import HtmlUtils from 'edx-ui-toolkit/js/utils/html-utils';

import EnrollModel from '../models/course_enroll_model';
import UpgradeMessageView from './upgrade_message_view';
import CertificateStatusView from './certificate_status_view';
import ExpiredNotificationView from './expired_notification_view';
import CourseEnrollView from './course_enroll_view';
import EntitlementView from './course_entitlement_view';

import pageTpl from '../../../templates/learner_dashboard/course_card.underscore';

class CourseCardView extends Backbone.View {
  constructor(options) {
    const defaults = {
      className: 'program-course-card',
    };
    super(Object.assign({}, defaults, options));
  }

  initialize(options) {
    this.tpl = HtmlUtils.template(pageTpl);
    this.enrollModel = new EnrollModel();
    if (options.context) {
      this.urlModel = new Backbone.Model(options.context.urls);
      this.enrollModel.urlRoot = this.urlModel.get('commerce_api_url');
    }
    this.context = options.context || {};
    this.collectionCourseStatus = this.context.collectionCourseStatus || '';
    this.entitlement = this.model.get('user_entitlement');

    this.render();
    this.listenTo(this.model, 'change', this.render);
  }

  render() {
    const data = $.extend(this.model.toJSON(), {
      enrolled: this.context.enrolled || '',
    });
    HtmlUtils.setHtml(this.$el, this.tpl(data));
    this.postRender();
  }

  postRender() {
    const $upgradeMessage = this.$('.upgrade-message');
    const $certStatus = this.$('.certificate-status');
    const $expiredNotification = this.$('.expired-notification');
    const courseKey = this.model.get('course_run_key');
    const expired = this.model.get('expired');
    const canUpgrade = this.model.get('upgrade_url') && !(expired === true);
    const courseUUID = this.model.get('uuid');
    const containerSelector = `#course-${courseUUID}`;

    this.enrollView = new CourseEnrollView({
      $parentEl: this.$('.course-actions'),
      model: this.model,
      collectionCourseStatus: this.collectionCourseStatus,
      urlModel: this.urlModel,
      enrollModel: this.enrollModel,
    });

    if (this.entitlement) {
      this.sessionSelectionView = new EntitlementView({
        el: this.$(`${containerSelector} .course-entitlement-selection-container`),
        $parentEl: this.$el,
        courseCardModel: this.model,
        enrollModel: this.enrollModel,
        triggerOpenBtn: '.course-details .change-session',
        courseCardMessages: '',
        courseImageLink: '',
        courseTitleLink: `${containerSelector} .course-details .course-title`,
        dateDisplayField: `${containerSelector} .course-details .course-text`,
        enterCourseBtn: `${containerSelector} .view-course-button`,
        availableSessions: JSON.stringify(this.model.get('course_runs')),
        entitlementUUID: this.entitlement.uuid,
        currentSessionId: this.model.isEnrolledInSession() && !canUpgrade ? courseKey : null,
        enrollUrl: this.model.get('enroll_url'),
        courseHomeUrl: this.model.get('course_url'),
        expiredAt: this.entitlement.expired_at,
        daysUntilExpiration: this.entitlement.days_until_expiration,
      });
    }

    if (canUpgrade) {
      this.upgradeMessage = new UpgradeMessageView({
        $el: $upgradeMessage,
        model: this.model,
      });

      $certStatus.remove();
    } else if (this.model.get('certificate_url') && !(expired === true)) {
      this.certificateStatus = new CertificateStatusView({
        $el: $certStatus,
        model: this.model,
      });

      $upgradeMessage.remove();
    } else {
      // Styles are applied to these elements which will be visible if they're empty.
      $upgradeMessage.remove();
      $certStatus.remove();
    }

    if (expired) {
      this.expiredNotification = new ExpiredNotificationView({
        $el: $expiredNotification,
        model: this.model,
      });
    }
  }
}

export default CourseCardView;
