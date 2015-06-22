;(function (define) {

define([
    'jquery',
    'underscore',
    'backbone',
    'gettext'
], function ($, _, Backbone, gettext) {

   'use strict';

    return Backbone.View.extend({
        initialize: function (options) {
            this.$el = options.el;
            this.model = options.model;
            this.templateId = options.proctored_template;
            this.template = null;
            this.timerId = null;

            var template_html = $(this.templateId).text();
            if(template_html !== null) {
                /* don't assume this backbone view is running on a page with the underscore templates */
                this.template = _.template(template_html);
            }
        },

        render: function () {
            if(this.template !== null) {
                var html = this.template(this.model.toJSON());
                this.$el.html(html);
                this.$el.show();
                this.updateRemainingTime(this);
                this.timerId = setInterval(this.updateRemainingTime, 1000, this);
                window.onbeforeunload = this.unloadMessage;

            }
            return this;
        },

        updateRemainingTime: function(self) {
            self.$el.find('div.exam-timer').removeClass("low-time warning critical");
            self.$el.find('div.exam-timer').addClass(self.model.getRemainingTimeState());
            self.$el.find('span#time_remaining_id b').html(self.model.getFormattedRemainingTime());
            if (self.model.getRemainingSeconds()<=0) {
                clearInterval(self.timerId); // stop the timer once the time finishes.
                window.onbeforeunload = null;
            }
        },
        unloadMessage: function  () {
            return "If you leave, any information you've entered may be\n" +
                "lost. Additionally, closing this window, regardless of\n" +
                "you being done with your work, will end your proctoring session.";
        }
    });
});


})(define || RequireJS.define);
