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
             CourseEnrollView,
             pageTpl
         ) {
             return Backbone.View.extend({
                 className: 'course-card card',

                 tpl: HtmlUtils.template(pageTpl),

                 initialize: function(options) {
                     this.enrollModel = new EnrollModel();
                     if (options.context && options.context.urls) {
                         this.urlModel = new Backbone.Model(options.context.urls);
                         this.enrollModel.urlRoot = this.urlModel.get('commerce_api_url');
                     }
                     this.render();
                     this.listenTo(this.model, 'change', this.render);
                 },

                 render: function() {
                     var filledTemplate = this.tpl(this.model.toJSON());
                     HtmlUtils.setHtml(this.$el, filledTemplate);
                     this.postRender();
                 },

                 postRender: function() {
                     var $upgradeMessage = this.$('.upgrade-message'),
                         $certStatus = this.$('.certificate-status');

                     this.enrollView = new CourseEnrollView({
                         $parentEl: this.$('.course-actions'),
                         model: this.model,
                         urlModel: this.urlModel,
                         enrollModel: this.enrollModel
                     });

                     if (this.model.get('upgrade_url')) {
                         this.upgradeMessage = new UpgradeMessageView({
                             $el: $upgradeMessage,
                             model: this.model
                         });

                         $certStatus.remove();
                     } else if (this.model.get('certificate_url')) {
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
                 }
             });
         }
    );
}).call(this, define || RequireJS.define);
