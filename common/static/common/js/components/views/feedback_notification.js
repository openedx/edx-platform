(function(define) {
    'use strict';
    define(['jquery', 'underscore', 'underscore.string', 'common/js/components/views/feedback'],
        function($, _, str, SystemFeedbackView) {
            var Notification = SystemFeedbackView.extend({
                options: $.extend({}, SystemFeedbackView.prototype.options, {
                    type: 'notification',
                    closeIcon: false
                })
            });

        // create Notification.Warning, Notification.Confirmation, etc
            var capitalCamel, intents;
            capitalCamel = _.compose(str.capitalize, str.camelize);
            intents = ['warning', 'error', 'confirmation', 'announcement', 'step-required', 'help', 'mini'];
            _.each(intents, function(intent) {
                var subclass;
                subclass = Notification.extend({
                    options: $.extend({}, Notification.prototype.options, {
                        intent: intent
                    })
                });
                Notification[capitalCamel(intent)] = subclass;
            });

        // set more sensible defaults for Notification.Mini views
            var miniOptions = Notification.Mini.prototype.options;
            miniOptions.minShown = 1250;
            miniOptions.closeIcon = false;

            return Notification;
        });
}).call(this, define || RequireJS.define);
