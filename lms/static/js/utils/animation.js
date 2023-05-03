(function() {
    this.AnimationUtil = (function() {
        function AnimationUtil() {}
        AnimationUtil.triggerAnimation = function(messageElement) {
            // The following lines are necessary to re-trigger the CSS animation on span.action-toggle-message
            // To see how it works, please see `Another JavaScript Method to Restart a CSS Animation`
            // at https://css-tricks.com/restart-css-animation/
            messageElement.removeClass('is-fleeting');
            messageElement.offset().width = messageElement.offset().width;
            messageElement.addClass('is-fleeting');
        };
        return AnimationUtil;
    }).call(this);
}).call(this);

