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
                         expired = this.model.get('expired');

                     this.enrollView = new CourseEnrollView({
                         $parentEl: this.$('.course-actions'),
                         model: this.model,
                         urlModel: this.urlModel,
                         enrollModel: this.enrollModel
                     });

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
