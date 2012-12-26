// Wrapper for RequireJS. It will make the standard requirejs(), require(), and
// define() functions from Require JS available inside the anonymous function.
//
// See https://edx-wiki.atlassian.net/wiki/display/LMS/Integration+of+Require+JS+into+the+system
(function (requirejs, require, define) {

define(['logme'], function (logme) {
    return updateInput;

    function updateInput(state) {
        var inputEl, stateStr, targets;

        if (state.individualTargets === false) {
            stateStr = JSON.stringify({
                'individualTargets': false,
                'draggables': state.draggables
            });
        } else {
            targets = [];
            (function (c1) {
                while (c1 < state.targets.length) {
                    targets.push({
                        'id': state.targets[c1].id,
                        'draggables': state.targets[c1].draggable
                    });

                    c1 += 1;
                }
            }(0));

            stateStr = JSON.stringify({
                'individualTargets': true,
                'targets': targets
            });
        }

        inputEl = $('#input_' + state.problemId);
        inputEl.val(stateStr);
    }

});

// End of wrapper for RequireJS. As you can see, we are passing
// namespaced Require JS variables to an anonymous function. Within
// it, you can use the standard requirejs(), require(), and define()
// functions as if they were in the global namespace.
}(RequireJS.requirejs, RequireJS.require, RequireJS.define)); // End-of: (function (requirejs, require, define)
