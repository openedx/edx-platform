// Wrapper for RequireJS. It will make the standard requirejs(), require(), and
// define() functions from Require JS available inside the anonymous function.
//
// See https://edx-wiki.atlassian.net/wiki/display/LMS/Integration+of+Require+JS+into+the+system
(function (requirejs, require, define) {

define(['logme'], function (logme) {
    return {
        'check': check,
        'update': update
    };

    function update(state) {
        var draggables, tempObj;

        draggables = [];

        if (state.config.individualTargets === false) {
            (function (c1) {
                while (c1 < state.draggables.length) {
                    if (state.draggables[c1].x !== -1) {
                        tempObj = {};
                        tempObj[state.draggables[c1].id] = [
                            state.draggables[c1].x,
                            state.draggables[c1].y
                        ];
                        draggables.push(tempObj);
                        tempObj = null;
                    }

                    c1 += 1;
                }
            }(0));
        } else {
            (function (c1) {
                while (c1 < state.targets.length) {
                    (function (c2) {
                        while (c2 < state.targets[c1].draggableList.length) {
                            tempObj = {};
                            tempObj[state.targets[c1].draggableList[c2].id] = state.targets[c1].id;
                            draggables.push(tempObj);
                            tempObj = null;

                            c2 += 1;
                        }
                    }(0));

                    c1 += 1;
                }
            }(0));
        }

        $('#input_' + state.problemId).val(JSON.stringify({'draggables': draggables}));
    }

    // Check if input has an answer from server. If yes, then position
    // all draggables according to answer.
    function check(state) {
        var inputElVal;

        inputElVal = $('#input_' + state.problemId).val();
        if (inputElVal.length === 0) {
            return false;
        }

        repositionDraggables(state, JSON.parse(inputElVal));

        return true;
    }

    function getUseTargets(answer) {
        if ($.isArray(answer.draggables) === false) {
            logme('ERROR: answer.draggables is not an array.');

            return;
        } else if (answer.draggables.length === 0) {
            return;
        }

        if ($.isPlainObject(answer.draggables[0]) === false) {
            logme('ERROR: answer.draggables array does not contain objects.');

            return;
        }

        for (c1 in answer.draggables[0]) {
            if (answer.draggables[0].hasOwnProperty(c1) === false) {
                continue;
            }

            if (typeof answer.draggables[0][c1] === 'string') {
                // use_targets = true;

                return true;
            } else if (
                ($.isArray(answer.draggables[0][c1]) === true) &&
                (answer.draggables[0][c1].length === 2)
            ) {
                // use_targets = false;

                return false;
            } else {
                logme('ERROR: answer.draggables[0] is inconsidtent.');

                return;
            }
        }

        logme('ERROR: answer.draggables[0] is an empty object.');

        return;
    }

    function processAnswerTargets(state, answer) {
        var draggableId, draggable, targetId, target;

        (function (c1) {
            while (c1 < answer.draggables.length) {
                for (draggableId in answer.draggables[c1]) {
                    if (answer.draggables[c1].hasOwnProperty(draggableId) === false) {
                        continue;
                    }

                    if ((draggable = getById(state, 'draggables', draggableId)) === null) {
                        logme(
                            'ERROR: In answer there exists a ' +
                            'draggable ID "' + draggableId + '". No ' +
                            'draggable with this ID could be found.'
                        );

                        continue;
                    }

                    targetId = answer.draggables[c1][draggableId];
                    if ((target = getById(state, 'targets', targetId)) === null) {
                        logme(
                            'ERROR: In answer there exists a target ' +
                            'ID "' + targetId + '". No target with this ' +
                            'ID could be found.'
                        );

                        continue;
                    }

                    draggable.moveDraggableTo('target', target);
                }

                c1 += 1;
            }
        }(0));
    }

    function processAnswerPositions(state, answer) {
        var draggableId, draggable;

        (function (c1) {
            while (c1 < answer.draggables.length) {
                for (draggableId in answer.draggables[c1]) {
                    if (answer.draggables[c1].hasOwnProperty(draggableId) === false) {
                        continue;
                    }

                    if ((draggable = getById(state, 'draggables', draggableId)) === null) {
                        logme(
                            'ERROR: In answer there exists a ' +
                            'draggable ID "' + draggableId + '". No ' +
                            'draggable with this ID could be found.'
                        );

                        continue;
                    }

                    draggable.moveDraggableTo('XY', {
                        'x': answer.draggables[c1][draggableId][0],
                        'y': answer.draggables[c1][draggableId][1]
                    });
                }

                c1 += 1;
            }
        }(0));
    }

    function repositionDraggables(state, answer) {
        if (answer.draggables.length === 0) {
            return;
        }

        if (state.config.individualTargets !== getUseTargets(answer)) {
            logme('ERROR: JSON config is not consistent with server response.');

            return;
        }

        if (state.config.individualTargets === true) {
            processAnswerTargets(state, answer);
        } else if (state.config.individualTargets === false) {
            processAnswerPositions(state, answer);
        }
    }

    function getById(state, type, id) {
        return (function (c1) {
            while (c1 < state[type].length) {
                if (type === 'draggables') {
                    if ((state[type][c1].id === id) && (state[type][c1].isOriginal === true)) {
                        return state[type][c1];
                    }
                } else { // 'targets'
                    if (state[type][c1].id === id) {
                        return state[type][c1];
                    }
                }

                c1 += 1;
            }

            return null;
        }(0));
    }
});

// End of wrapper for RequireJS. As you can see, we are passing
// namespaced Require JS variables to an anonymous function. Within
// it, you can use the standard requirejs(), require(), and define()
// functions as if they were in the global namespace.
}(RequireJS.requirejs, RequireJS.require, RequireJS.define)); // End-of: (function (requirejs, require, define)
