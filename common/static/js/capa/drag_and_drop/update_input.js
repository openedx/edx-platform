// Wrapper for RequireJS. It will make the standard requirejs(), require(), and
// define() functions from Require JS available inside the anonymous function.
//
// See https://edx-wiki.atlassian.net/wiki/display/LMS/Integration+of+Require+JS+into+the+system
(function (requirejs, require, define) {

define(['logme'], function (logme) {
    return updateInput;

    function updateInput(state, checkFirst) {
        var inputEl, stateStr, targets, draggables, c1, c2, tempObj;

        if (checkFirst === true) {
            if (checkIfHasAnswer() === true) {
                return;
            }
        }

        draggables = [];

        if (state.individualTargets === false) {
            for (c1 = 0; c1 < state.draggables.length; c1++) {
                if (state.draggables[c1].x !== -1) {
                    tempObj = {};
                    tempObj[state.draggables[c1].id] = [
                        state.draggables[c1].x,
                        state.draggables[c1].y
                    ];

                    draggables.push(tempObj);
                }
            }

            stateStr = JSON.stringify({
                'use_targets': false,
                'draggables': draggables
            });
        } else {
            for (c1 = 0; c1 < state.targets.length; c1++) {
                for (c2 = 0; c2 < state.targets[c1].draggable.length; c2++) {
                    tempObj = {};
                    tempObj[state.targets[c1].draggable[c2]] = state.targets[c1].id;

                    draggables.push(tempObj);
                }
            }

            stateStr = JSON.stringify({
                'use_targets': true,
                'draggables': draggables
            });
        }

        inputEl = $('#input_' + state.problemId);
        inputEl.val(stateStr);

        logme(inputEl.val());

        return;

        // Check if input has an answer from server. If yes, then position
        // all draggables according to answer.
        function checkIfHasAnswer() {
            var inputElVal;

            inputElVal = $('#input_' + state.problemId).val();
            if (inputElVal.length === 0) {
                return false;
            }

            repositionDraggables(JSON.parse(inputElVal));

            return true;
        }

        function repositionDraggables(answer) {
            var draggableId, draggable, targetId, target, draggablePosition,
                c1;

            logme(answer);

            if (
                ((typeof answer.use_targets === 'boolean') && (answer.use_targets === true)) ||
                ((typeof answer.use_targets === 'string') && (answer.use_targets === 'true'))
            ) {
                for (c1 = 0; c1 < answer.draggables.length; c1++) {
                    for (draggableId in answer.draggables[c1]) {
                        if ((draggable = getDraggableById(draggableId)) === null) {
                            logme('ERROR: In answer there exists a draggable ID "' + draggableId + '". No draggable with this ID could be found.');

                            continue;
                        }

                        targetId = answer.draggables[c1][draggableId];
                        if ((target = getTargetById(targetId)) === null) {
                            logme('ERROR: In answer there exists a target ID "' + targetId + '". No target with this ID could be found.');

                            continue;
                        }


                        draggable.setInContainer(false);

                        draggable.el.detach();
                        draggable.el.css('border', 'none');
                        draggable.el.css('position', 'absolute');
                        draggable.el.css('left', answer.draggables[c1][draggableId][0] - 50);
                        draggable.el.css('top', answer.draggables[c1][draggableId][1] - 50);

                        draggable.el.css('left', target.offset.left + 0.5 * target.w - 50);
                        draggable.el.css('top', target.offset.top + 0.5 * target.h - 50);

                        draggable.el.appendTo(state.baseImageEl.parent());

                        draggable.setOnTarget(target);
                        target.draggable.push(draggableId);
                    }
                }
            } else if (
                ((typeof answer.use_targets === 'boolean') && (answer.use_targets === false)) ||
                ((typeof answer.use_targets === 'string') && (answer.use_targets === 'false'))
            ) {
                for (c1 = 0; c1 < answer.draggables.length; c1++) {
                    for (draggableId in answer.draggables[c1]) {
                        if ((draggable = getDraggableById(draggableId)) === null) {
                            logme('ERROR: In answer there exists a draggable ID "' + draggableId + '". No draggable with this ID could be found.');

                            continue;
                        }

                        draggable.setInContainer(false);

                        draggable.el.detach();
                        draggable.el.css('border', 'none');
                        draggable.el.css('position', 'absolute');
                        draggable.el.css('left', answer.draggables[c1][draggableId][0] - 50);
                        draggable.el.css('top', answer.draggables[c1][draggableId][1] - 50);
                        draggable.el.appendTo(state.baseImageEl.parent());

                        draggable.x = answer.draggables[c1][draggableId][0];
                        draggable.y = answer.draggables[c1][draggableId][1];
                    }
                }
            } else {
                logme('ERROR: The type of answer.targets is not supported. answer.targets = ', answer.targets);

                return;
            }

            state.updateArrowOpacity();
        }

        return;

        function getDraggableById(id) {
            var c1;

            for (c1 = 0; c1 < state.draggables.length; c1 += 1) {
                if (state.draggables[c1].id === id) {
                    return state.draggables[c1];
                }
            }

            return null;
        }

        function getTargetById(id) {
            var c1;

            for (c1 = 0; c1 < state.targets.length; c1 += 1) {
                if (state.targets[c1].id === id) {
                    return state.targets[c1];
                }
            }

            return null;
        }
    }
});

// End of wrapper for RequireJS. As you can see, we are passing
// namespaced Require JS variables to an anonymous function. Within
// it, you can use the standard requirejs(), require(), and define()
// functions as if they were in the global namespace.
}(RequireJS.requirejs, RequireJS.require, RequireJS.define)); // End-of: (function (requirejs, require, define)
