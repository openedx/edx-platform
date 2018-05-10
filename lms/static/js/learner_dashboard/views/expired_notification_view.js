(function(define) {
    'use strict';
    define(['backbone',
        'jquery',
        'underscore',
        'gettext',
        'edx-ui-toolkit/js/utils/html-utils',
        'text!../../../templates/learner_dashboard/expired_notification.underscore'
    ],
         function(
             Backbone,
             $,
             _,
             gettext,
             HtmlUtils,
             expiredNotificationTpl
         ) {
             return Backbone.View.extend({
                 expiredNotificationTpl: HtmlUtils.template(expiredNotificationTpl),

                 initialize: function(options) {
                     this.$el = options.$el;
                     this.render();
                 },

                 render: function() {
                     var data = this.model.toJSON();
                     HtmlUtils.setHtml(this.$el, this.expiredNotificationTpl(data));
                 }
             });
         }
    );
}).call(this, define || RequireJS.define);
