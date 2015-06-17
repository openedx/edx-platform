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
            this.template = _.template($(this.templateId).html());
            this.timerId = null;
        },

        render: function () {
            var html = this.template(this.model.toJSON());
            this.$el.html(html);
            this.$el.show();
            this.timerId = setInterval(this.updateRemainingTime, 1000, this);
            return this;
        },
        updateRemainingTime: function(self) {
            //var remainingSeconds = self.model.get('time_remaining_seconds') - 1;
            //self.model.set('time_remaining_seconds', remainingSeconds);
            //var date = new Date();
            //var hours = date.getHours();
            //if (hours < 10) hours = '0'+hours;
            //
            //
            //var minutes = date.getMinutes();
            //if (minutes < 10) minutes = '0'+minutes;
            //
            //var seconds = date.getSeconds();
            //if (seconds < 10) seconds = '0'+seconds;

            var state = self.model.getRemainingTimeState(); // normal=blue/low=orange/critically_low=red.
            switch (state) {
                case 'normal':
                    // make blue
                    break;
                case 'low':
                    // make orange;
                    break;
                case 'criticallyLow':
                    // make red;
                    break;
            }
            self.$el.find('span#time_remaining_id b').html(self.model.getFormattedRemainingTime());
        }

    });

});


})(define || RequireJS.define);
