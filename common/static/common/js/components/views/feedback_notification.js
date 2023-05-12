(function(define) {
    'use strict';

    define(['jquery', 'underscore', 'underscore.string', './feedback'],
        function($, _, str, SystemFeedbackView) {
            // eslint-disable-next-line no-var
            var Notification = SystemFeedbackView.extend({
                options: $.extend({}, SystemFeedbackView.prototype.options, {
                    type: 'notification',
                    closeIcon: false
                })
            });

            // create Notification.Warning, Notification.Confirmation, etc
            // eslint-disable-next-line no-var
            var capitalCamel, intents, miniOptions;
            capitalCamel = _.compose(str.capitalize, str.camelize);
            intents = ['warning', 'error', 'confirmation', 'announcement', 'step-required', 'help', 'mini'];
            _.each(intents, function(intent) {
                // eslint-disable-next-line no-var
                var subclass;
                subclass = Notification.extend({
                    options: $.extend({}, Notification.prototype.options, {
                        intent: intent
                    })
                });
                Notification[capitalCamel(intent)] = subclass;
            });

            // set more sensible defaults for Notification.Mini views
            miniOptions = Notification.Mini.prototype.options;
            miniOptions.minShown = 1250;
            miniOptions.closeIcon = false;

            return Notification;
        }
    );
// eslint-disable-next-line no-undef
}).call(this, define || RequireJS.define);
