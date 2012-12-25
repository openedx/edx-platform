// Wrapper for RequireJS. It will make the standard requirejs(), require(), and
// define() functions from Require JS available inside the anonymous function.
//
// See https://edx-wiki.atlassian.net/wiki/display/LMS/Integration+of+Require+JS+into+the+system
(function (requirejs, require, define) {

define(['logme'], function (logme) {
    return Targets;

    function Targets(state) {
        (function (c1) {
            while (c1 < state.config.targets.length) {
                processTarget(state.config.targets[c1]);
                c1 += 1;
            }
        }(0));

        return;

        function processTarget(obj) {
            var targetElOffset, tEl, left, top;

            if (state.targetEl_loaded === false) {
                window.setTimeout(function () {
                    processTarget(obj);
                }, 50);
                return;
            }

            left = obj.x + 0.5 * (state.targetEl.parent().width() - state.targetEl_width);
            top = obj.y

            tEl = $(
                '<div ' +
                    'style=" ' +
                        'display: block; ' +
                        'position: absolute; ' +
                        'width: ' + obj.w + 'px; ' +
                        'height: ' + obj.h + 'px; ' +
                        'top: ' + top + 'px; ' +
                        'left: ' + left + 'px; ' +
                        'border: 1px solid black; ' +
                    '" ' +
                    'data-target-id="' + obj.id + '" ' +
                '></div>'
            );

            tEl.appendTo(state.targetEl.parent());
        }
    }
});

// End of wrapper for RequireJS. As you can see, we are passing
// namespaced Require JS variables to an anonymous function. Within
// it, you can use the standard requirejs(), require(), and define()
// functions as if they were in the global namespace.
}(RequireJS.requirejs, RequireJS.require, RequireJS.define)); // End-of: (function (requirejs, require, define)
