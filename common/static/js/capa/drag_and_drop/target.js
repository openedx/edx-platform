// Wrapper for RequireJS. It will make the standard requirejs(), require(), and
// define() functions from Require JS available inside the anonymous function.
//
// See https://edx-wiki.atlassian.net/wiki/display/LMS/Integration+of+Require+JS+into+the+system
(function (requirejs, require, define) {

define(['logme'], function (logme) {
    return Target;

    function Target(state) {
        var targetImgSrc, targetElContainer, mouseMoveDiv;

        targetImgSrc = state.config.imageDir + '/' + state.config.target;

        targetElContainer = $(
            '<div ' +
                'style=" ' +
                    'text-align: center; ' +
                '" ' +
            '></div>'
        );

        state.targetEl = $(
            '<img ' +
                'src="' + targetImgSrc + '" ' +
            '/>'
        );
        state.targetEl.appendTo(targetElContainer);

        state.targetEl.mousemove(
            function (event) {
                mouseMoveDiv.html(
                    '[' + event.offsetX + ', ' + event.offsetY + ']'
                );
            }
        );

        mouseMoveDiv = $(
            '<div ' +
                'style=" ' +
                    'clear: both; ' +
                    'width: auto; ' +
                    'height: 25px; ' +
                    'text-align: center; ' +
                '" ' +
            '>[0, 0]</div>'
        );
        mouseMoveDiv.appendTo(targetElContainer);

        targetElContainer.appendTo(state.containerEl);

        state.targetElOffset = state.targetEl.offset();
    }
});

// End of wrapper for RequireJS. As you can see, we are passing
// namespaced Require JS variables to an anonymous function. Within
// it, you can use the standard requirejs(), require(), and define()
// functions as if they were in the global namespace.
}(RequireJS.requirejs, RequireJS.require, RequireJS.define)); // End-of: (function (requirejs, require, define)
