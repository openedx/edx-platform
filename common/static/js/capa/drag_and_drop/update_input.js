// Wrapper for RequireJS. It will make the standard requirejs(), require(), and
// define() functions from Require JS available inside the anonymous function.
//
// See https://edx-wiki.atlassian.net/wiki/display/LMS/Integration+of+Require+JS+into+the+system
(function (requirejs, require, define) {

define(['logme'], function (logme) {
    return updateInput;

    function updateInput(state) {
        var inputEl, stateStr, targets, draggables, c1, c2, tempObj;

        draggables = [];

        if (state.individualTargets === false) {
            for (c1 = 0; c1 < state.draggables.length; c1++) {
                if (state.draggables[c1].x !== -1) {
                    tempObj = {};
                    tempObj[state.draggables[c1].id] = {
                        'x': state.draggables[c1].x,
                        'y': state.draggables[c1].y
                    };

                    draggables.push(tempObj);
                }
            }

            stateStr = JSON.stringify({
                'targets': false,
                'draggables': draggables
            });
        } else {
            for (c1 = 0; c1 < state.targets.length; c1++) {
                for (c2 = 0; c2 < state.targets[c1].draggable.length; c2++) {
                    tempObj = {};
                    tempObj[state.targets[c1].draggable[c2]] = state.draggables[c1].id;

                    draggables.push(tempObj);
                }
            }

            stateStr = JSON.stringify({
                'targets': true,
                'draggables': draggables
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
