// Wrapper for RequireJS. It will make the standard requirejs(), require(), and
// define() functions from Require JS available inside the anonymous function.
//
// See https://edx-wiki.atlassian.net/wiki/display/LMS/Integration+of+Require+JS+into+the+system
(function (requirejs, require, define) {

define(['logme'], function (logme) {
    return Targets;

    function Targets(state) {
        var c1;

        state.targets = [];

        for (c1 = 0; c1 < state.config.targets.length; c1++) {
            processTarget(state.config.targets[c1]);
        }

        return;

        function processTarget(obj) {
            var targetEl, borderCss;

            borderCss = '';
            if (state.config.targetOutline === true) {
                borderCss = 'border: 1px dashed gray; ';
            }

            targetEl = $(
                '<div ' +
                    'style=" ' +
                        'display: block; ' +
                        'position: absolute; ' +
                        'width: ' + obj.w + 'px; ' +
                        'height: ' + obj.h + 'px; ' +
                        'top: ' + obj.y + 'px; ' +
                        'left: ' + obj.x + 'px; ' +
                        borderCss +
                    '" ' +
                    'data-target-id="' + obj.id + '" ' +
                '></div>'
            );

            targetEl.appendTo(state.baseImageEl.parent());

            state.targets.push({
                'id': obj.id,

                'w': obj.w,
                'h': obj.h,

                'el': targetEl,
                'offset': targetEl.position(),

                'draggable': []
            });
        }
    }
});

// End of wrapper for RequireJS. As you can see, we are passing
// namespaced Require JS variables to an anonymous function. Within
// it, you can use the standard requirejs(), require(), and define()
// functions as if they were in the global namespace.
}(RequireJS.requirejs, RequireJS.require, RequireJS.define)); // End-of: (function (requirejs, require, define)
