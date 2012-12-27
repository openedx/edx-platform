// Wrapper for RequireJS. It will make the standard requirejs(), require(), and
// define() functions from Require JS available inside the anonymous function.
//
// See https://edx-wiki.atlassian.net/wiki/display/LMS/Integration+of+Require+JS+into+the+system
(function (requirejs, require, define) {

define(['logme', 'update_input'], function (logme, updateInput) {
    return Targets;

    function Targets(state) {
        state.targets = [];

        (function (c1) {
            while (c1 < state.config.targets.length) {
                processTarget(state.config.targets[c1]);
                c1 += 1;
            }
        }(0));

        return;

        function processTarget(obj) {
            var baseImageElOffset, tEl, left, borderCss;

            if (state.baseImageElWidth === null) {
                window.setTimeout(function () {
                    processTarget(obj);
                }, 50);
                return;
            }

            left = obj.x + 0.5 * (state.baseImageEl.parent().width() - state.baseImageElWidth);

            borderCss = '';
            if (state.config.target_outline === true) {
                borderCss = 'border: 1px dashed gray; ';
            }

            tEl = $(
                '<div ' +
                    'style=" ' +
                        'display: block; ' +
                        'position: absolute; ' +
                        'width: ' + obj.w + 'px; ' +
                        'height: ' + obj.h + 'px; ' +
                        'top: ' + obj.y + 'px; ' +
                        'left: ' + left + 'px; ' +
                        borderCss +
                    '" ' +
                    'data-target-id="' + obj.id + '" ' +
                '></div>'
            );

            tEl.appendTo(state.baseImageEl.parent());

            state.targets.push({
                'id': obj.id,
                'offset': tEl.position(),
                'w': obj.w,
                'h': obj.h,
                'el': tEl,
                'draggable': []
            });

            if (state.individualTargets === true) {
                updateInput(state);
            }
        }
    }
});

// End of wrapper for RequireJS. As you can see, we are passing
// namespaced Require JS variables to an anonymous function. Within
// it, you can use the standard requirejs(), require(), and define()
// functions as if they were in the global namespace.
}(RequireJS.requirejs, RequireJS.require, RequireJS.define)); // End-of: (function (requirejs, require, define)
