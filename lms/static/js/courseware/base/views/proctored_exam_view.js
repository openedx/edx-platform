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
            this.template_html = $(this.templateId).html();
            if(this.template_html !== null) {
                this.template = _.template(this.template_el.html());
            } else {
                this.template = null;
            }

            this.timerId = null;
        },

        render: function () {
            if(this.template !== null) {
                var html = this.template(this.model.toJSON());
                this.$el.html(html);
                this.$el.show();
                this.updateRemainingTime(this);
                this.timerId = setInterval(this.updateRemainingTime, 1000, this);
            }
            return this;
        },

        updateRemainingTime: function(self) {
            self.$el.find('div.exam-timer').removeClass("low-time warning critical");
            self.$el.find('div.exam-timer').addClass(self.model.getRemainingTimeState());
            self.$el.find('span#time_remaining_id b').html(self.model.getFormattedRemainingTime());
            if (self.model.getRemainingSeconds()<=0) {
                clearInterval(this.timerId); // stop the timer once the time finishes.
            }
        }
    });
});


})(define || RequireJS.define);
