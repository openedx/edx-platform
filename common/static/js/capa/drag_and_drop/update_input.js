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
                    tempObj[state.targets[c1].draggable[c2]] =
                        state.targets[c1].id;

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
            var draggableId, draggable, targetId, target, c1, offset;

            offset = 0;
            if (state.config.targetOutline === true) {
                offset = 1;
            }

            if (
                (
                    (typeof answer.use_targets === 'boolean') &&
                    (answer.use_targets === true)
                ) ||
                (
                    (typeof answer.use_targets === 'string') &&
                    (answer.use_targets === 'true')
                )
            ) {
                for (c1 = 0; c1 < answer.draggables.length; c1++) {
                    for (draggableId in answer.draggables[c1]) {
                        if (
                            (draggable = getDraggableById(draggableId)) ===
                            null
                        ) {
                            logme(
                                'ERROR: In answer there exists a ' +
                                'draggable ID "' + draggableId + '". No ' +
                                'draggable with this ID could be found.'
                            );

                            continue;
                        }

                        targetId = answer.draggables[c1][draggableId];
                        if ((target = getTargetById(targetId)) === null) {
                            logme(
                                'ERROR: In answer there exists a target ' +
                                'ID "' + targetId + '". No target with this ' +
                                'ID could be found.'
                            );

                            continue;
                        }

                        (function (draggableId, draggable, targetId, target) {
                            moveDraggableToBaseImage();
                            return;

                            function moveDraggableToBaseImage() {
                                if (draggable.hasLoaded === false) {
                                    setTimeout(moveDraggableToBaseImage, 50);
                                    return;
                                }

                                draggable.setInContainer(false);
                                draggable.containerEl.hide();

                                draggable.iconEl.detach();
                                draggable.iconEl.css(
                                    'width',
                                    draggable.iconWidth
                                );
                                draggable.iconEl.css(
                                    'height',
                                    draggable.iconHeight
                                );
                                draggable.iconEl.css(
                                    'left',
                                    target.offset.left + 0.5 * target.w -
                                        draggable.iconWidth * 0.5 + offset
                                );
                                draggable.iconEl.css(
                                    'top',
                                    target.offset.top + 0.5 * target.h -
                                        draggable.iconHeight * 0.5 + offset
                                );
                                draggable.iconEl.appendTo(
                                    state.baseImageEl.parent()
                                );

                                if (draggable.labelEl !== null) {
                                    draggable.labelEl.detach();
                                    draggable.labelEl.css(
                                        'left',
                                        target.offset.left + 0.5 * target.w -
                                            draggable.labelWidth * 0.5 + offset
                                    );
                                    draggable.labelEl.css(
                                        'top',
                                        target.offset.top + 0.5 * target.h +
                                            draggable.iconHeight * 0.5 + 5 +
                                            offset
                                    );
                                    draggable.labelEl.appendTo(
                                        state.baseImageEl.parent()
                                    );
                                }

                                draggable.setOnTarget(target);
                                target.draggable.push(draggableId);

                                state.numDraggablesInSlider -= 1;
                                state.updateArrowOpacity();
                            }
                        }(draggableId, draggable, targetId, target));
                    }
                }
            } else if (
                (
                    (typeof answer.use_targets === 'boolean') &&
                    (answer.use_targets === false)
                ) ||
                (
                    (typeof answer.use_targets === 'string') &&
                    (answer.use_targets === 'false')
                )
            ) {
                for (c1 = 0; c1 < answer.draggables.length; c1++) {
                    for (draggableId in answer.draggables[c1]) {
                        if (
                            (draggable = getDraggableById(draggableId)) ===
                            null
                           ) {
                            logme(
                                'ERROR: In answer there exists a ' +
                                'draggable ID "' + draggableId + '". No ' +
                                'draggable with this ID could be found.'
                            );

                            continue;
                        }

                        (function (c1, draggableId, draggable) {
                            moveDraggableToBaseImage();
                            return;

                            function moveDraggableToBaseImage() {
                                if (draggable.hasLoaded === false) {
                                    setTimeout(moveDraggableToBaseImage, 50);
                                    return;
                                }

                                draggable.setInContainer(false);
                                draggable.containerEl.hide();

                                draggable.iconEl.detach();
                                draggable.iconEl.css(
                                    'width',
                                    draggable.iconWidth
                                );
                                draggable.iconEl.css(
                                    'height',
                                    draggable.iconHeight
                                );
                                draggable.iconEl.css(
                                    'left',
                                    answer.draggables[c1][draggableId][0] -
                                        draggable.iconWidth * 0.5 + offset
                                );
                                draggable.iconEl.css(
                                    'top',
                                    answer.draggables[c1][draggableId][1] -
                                        draggable.iconHeight * 0.5 + offset
                                );
                                draggable.iconEl.appendTo(
                                    state.baseImageEl.parent()
                                );

                                if (draggable.labelEl !== null) {
                                    draggable.labelEl.detach();
                                    draggable.labelEl.css(
                                        'left',
                                        answer.draggables[c1][draggableId][0] -
                                            draggable.labelWidth * 0.5 + offset
                                    );
                                    draggable.labelEl.css(
                                        'top',
                                        answer.draggables[c1][draggableId][1] -
                                            draggable.iconHeight * 0.5 +
                                            draggable.iconHeight + 5 + offset
                                    );
                                    draggable.labelEl.appendTo(
                                        state.baseImageEl.parent()
                                    );
                                }

                                draggable.x =
                                    answer.draggables[c1][draggableId][0];
                                draggable.y =
                                    answer.draggables[c1][draggableId][1];

                                state.numDraggablesInSlider -= 1;
                                state.updateArrowOpacity();
                            }
                        }(c1, draggableId, draggable));
                    }
                }
            } else {
                logme(
                    'ERROR: The type of answer.targets is not supported. ' +
                    'answer.targets = ', answer.targets
                );

                return;
            }
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
