;(function (define) {
    'use strict';
    define(["jquery", "underscore", "underscore.string", "common/js/components/views/feedback"],
        function($, _, str, SystemFeedbackView) {

        var Alert = SystemFeedbackView.extend({
            options: $.extend({}, SystemFeedbackView.prototype.options, {
                type: "alert"
            }),
            slide_speed: 900,
            show: function() {
                SystemFeedbackView.prototype.show.apply(this, arguments);
                this.$el.hide();
                this.$el.slideDown(this.slide_speed);
                return this;
            },
            hide: function () {
                this.$el.slideUp({
                    duration: this.slide_speed
                });
                setTimeout(_.bind(SystemFeedbackView.prototype.hide, this, arguments),
                           this.slideSpeed);
            }
        });

        // create Alert.Warning, Alert.Confirmation, etc
        var capitalCamel, intents;
        capitalCamel = _.compose(str.capitalize, str.camelize);
        intents = ["warning", "error", "confirmation", "announcement", "step-required", "help", "mini"];
        _.each(intents, function(intent) {
            var subclass;
            subclass = Alert.extend({
                options: $.extend({}, Alert.prototype.options, {
                    intent: intent
                })
            });
            Alert[capitalCamel(intent)] = subclass;
        });

        return Alert;
    });
}).call(this, define || RequireJS.define);
