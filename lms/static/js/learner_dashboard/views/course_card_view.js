(function(define) {
    'use strict';

    define(['backbone',
        'jquery',
        'underscore',
        'gettext',
        'edx-ui-toolkit/js/utils/html-utils',
        'js/learner_dashboard/models/course_enroll_model',
        'js/learner_dashboard/views/upgrade_message_view',
        'js/learner_dashboard/views/certificate_status_view',
        'js/learner_dashboard/views/expired_notification_view',
        'js/learner_dashboard/views/course_enroll_view',
        'js/learner_dashboard/views/course_entitlement_view',
        'text!../../../templates/learner_dashboard/course_card.underscore'
    ],
         function(
             Backbone,
             $,
             _,
             gettext,
             HtmlUtils,
             EnrollModel,
             UpgradeMessageView,
             CertificateStatusView,
             ExpiredNotificationView,
             CourseEnrollView,
             EntitlementView,
             pageTpl
         ) {
             return Backbone.View.extend({
                 className: 'program-course-card',

                 tpl: HtmlUtils.template(pageTpl),

                 initialize: function(options) {
                     this.enrollModel = new EnrollModel();
                     if (options.context) {
                         this.urlModel = new Backbone.Model(options.context.urls);
                         this.enrollModel.urlRoot = this.urlModel.get('commerce_api_url');
                     }
                     this.context = options.context || {};
                     this.grade = this.context.courseData.grades[this.model.get('course_run_key')];
                     this.grade = this.grade * 100;
                     this.collectionCourseStatus = this.context.collectionCourseStatus || '';
                     this.entitlement = this.model.get('user_entitlement');

                     this.render();
                     this.listenTo(this.model, 'change', this.render);
                 },

                 render: function() {
                     var data = $.extend(this.model.toJSON(), {
                         enrolled: this.context.enrolled || ''
                     });
                     HtmlUtils.setHtml(this.$el, this.tpl(data));
                     this.postRender();
                 },

                 postRender: function() {
                     var $upgradeMessage = this.$('.upgrade-message'),
                         $certStatus = this.$('.certificate-status'),
                         $expiredNotification = this.$('.expired-notification'),
                         expired = this.model.get('expired'),
                         courseUUID = this.model.get('uuid'),
                         containerSelector = '#course-' + courseUUID;

                     this.enrollView = new CourseEnrollView({
                         $parentEl: this.$('.course-actions'),
                         model: this.model,
                         grade: this.grade,
                         collectionCourseStatus: this.collectionCourseStatus,
                         urlModel: this.urlModel,
                         enrollModel: this.enrollModel
                     });

                     if (this.entitlement) {
                         this.sessionSelectionView = new EntitlementView({
                             el: this.$(containerSelector + ' .course-entitlement-selection-container'),
                             $parentEl: this.$el,
                             courseCardModel: this.model,
                             enrollModel: this.enrollModel,
                             triggerOpenBtn: '.course-details .change-session',
                             courseCardMessages: '',
                             courseImageLink: '',
                             courseTitleLink: containerSelector + ' .course-details .course-title',
                             dateDisplayField: containerSelector + ' .course-details .course-text',
                             enterCourseBtn: containerSelector + ' .view-course-button',
                             availableSessions: JSON.stringify(this.model.get('course_runs')),
                             entitlementUUID: this.entitlement.uuid,
                             currentSessionId: this.model.get('course_run_key'),
                             enrollUrl: this.model.get('enroll_url'),
                             courseHomeUrl: this.model.get('course_url')
                         });
                     }

                     if (this.model.get('upgrade_url') && !(expired === true)) {
                         this.upgradeMessage = new UpgradeMessageView({
                             $el: $upgradeMessage,
                             model: this.model
                         });

                         $certStatus.remove();
                     } else if (this.model.get('certificate_url') && !(expired === true)) {
                         this.certificateStatus = new CertificateStatusView({
                             $el: $certStatus,
                             model: this.model
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
                             model: this.model
                         });
                     }
                 }
             });
         }
    );
}).call(this, define || RequireJS.define);
