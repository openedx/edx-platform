;(function (define) {
    'use strict';
    define(["jquery", "underscore", "underscore.string", "common/js/components/views/feedback"],
        function($, _, str, SystemFeedbackView) {

            var Prompt = SystemFeedbackView.extend({
                options: $.extend({}, SystemFeedbackView.prototype.options, {
                    type: "prompt",
                    closeIcon: false,
                    icon: false
                }),
                render: function() {
                    if(!window.$body) { window.$body = $(document.body); }
                    if(this.options.shown) {
                        $body.addClass('prompt-is-shown');
                    } else {
                        $body.removeClass('prompt-is-shown');
                    }
                    // super() in Javascript has awkward syntax :(
                    return SystemFeedbackView.prototype.render.apply(this, arguments);
                },
                show: function() {
                    SystemFeedbackView.prototype.show.apply(this, arguments);
                    return this.inFocus();
                },

                hide: function() {
                    SystemFeedbackView.prototype.hide.apply(this, arguments);
                    return this.outFocus();
                }
            });

            // create Prompt.Warning, Prompt.Confirmation, etc
            var capitalCamel, intents;
            capitalCamel = _.compose(str.capitalize, str.camelize);
            intents = ["warning", "error", "confirmation", "announcement", "step-required", "help", "mini"];
            _.each(intents, function(intent) {
                var subclass;
                subclass = Prompt.extend({
                    options: $.extend({}, Prompt.prototype.options, {
                        intent: intent
                    })
                });
                Prompt[capitalCamel(intent)] = subclass;
            });

            return Prompt;
        });
}).call(this, define || RequireJS.define);
