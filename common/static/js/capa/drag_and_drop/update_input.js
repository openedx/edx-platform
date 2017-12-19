(function(requirejs, require, define) {
    define([], function() {
        return {
            check: check,
            update: update
        };

        function update(state) {
            var draggables, tempObj;

            draggables = [];

            if (state.config.individualTargets === false) {
                (function(c1) {
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
                (function(c1) {
                    while (c1 < state.targets.length) {
                        (function(c2) {
                            while (c2 < state.targets[c1].draggableList.length) {
                                tempObj = {};

                                if (state.targets[c1].type === 'base') {
                                    tempObj[state.targets[c1].draggableList[c2].id] = state.targets[c1].id;
                                } else {
                                    addTargetRecursively(tempObj, state.targets[c1].draggableList[c2], state.targets[c1]);
                                }
                                draggables.push(tempObj);
                                tempObj = null;

                                c2 += 1;
                            }
                        }(0));

                        c1 += 1;
                    }
                }(0));
            }

            $('#input_' + state.problemId).val(JSON.stringify(draggables));
        }

        function addTargetRecursively(tempObj, draggable, target) {
            if (target.type === 'base') {
                tempObj[draggable.id] = target.id;
            } else {
                tempObj[draggable.id] = {};
                tempObj[draggable.id][target.id] = {};

                addTargetRecursively(tempObj[draggable.id][target.id], target.draggableObj, target.draggableObj.onTarget);
            }
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

        function processAnswerTargets(state, answerSortedByDepth, minDepth, maxDepth, depth, i) {
            var baseDraggableId, baseDraggable, baseTargetId, baseTarget,
                layeredDraggableId, layeredDraggable, layeredTargetId, layeredTarget,
                chain;

            if (depth === 0) {
            // We are at the lowest depth? The end.

                return;
            }

            if (answerSortedByDepth.hasOwnProperty(depth) === false) {
            // We have a depth that ts not valid, we decrease the depth by one.
                processAnswerTargets(state, answerSortedByDepth, minDepth, maxDepth, depth - 1, 0);

                return;
            }

            if (answerSortedByDepth[depth].length <= i) {
            // We ran out of answers at this depth, go to the next depth down.
                processAnswerTargets(state, answerSortedByDepth, minDepth, maxDepth, depth - 1, 0);

                return;
            }

            chain = answerSortedByDepth[depth][i];

            baseDraggableId = Object.keys(chain)[0];

        // This is a hack. For now we will work with depths 1 and 3.
            if (depth === 1) {
                baseTargetId = chain[baseDraggableId];

                layeredTargetId = null;
                layeredDraggableId = null;

            // createBaseDraggableOnTarget(state, baseDraggableId, baseTargetId);
            } else if (depth === 3) {
                layeredDraggableId = baseDraggableId;

                layeredTargetId = Object.keys(chain[layeredDraggableId])[0];

                baseDraggableId = Object.keys(chain[layeredDraggableId][layeredTargetId])[0];

                baseTargetId = chain[layeredDraggableId][layeredTargetId][baseDraggableId];
            }

            checkBaseDraggable();

            return;

            function checkBaseDraggable() {
                if ((baseDraggable = getById(state, 'draggables', baseDraggableId, null, false, baseTargetId)) === null) {
                    createBaseDraggableOnTarget(state, baseDraggableId, baseTargetId, true, function() {
                        if ((baseDraggable = getById(state, 'draggables', baseDraggableId, null, false, baseTargetId)) === null) {
                            console.log('ERROR: Could not successfully create a base draggable on a base target.');
                        } else {
                            baseTarget = baseDraggable.onTarget;

                            if ((layeredTargetId === null) || (layeredDraggableId === null)) {
                                processAnswerTargets(state, answerSortedByDepth, minDepth, maxDepth, depth, i + 1);
                            } else {
                                checklayeredDraggable();
                            }
                        }
                    });
                } else {
                    baseTarget = baseDraggable.onTarget;

                    if ((layeredTargetId === null) || (layeredDraggableId === null)) {
                        processAnswerTargets(state, answerSortedByDepth, minDepth, maxDepth, depth, i + 1);
                    } else {
                        checklayeredDraggable();
                    }
                }
            }

            function checklayeredDraggable() {
                if ((layeredDraggable = getById(state, 'draggables', layeredDraggableId, null, false, layeredTargetId, baseDraggableId, baseTargetId)) === null) {
                    layeredDraggable = getById(state, 'draggables', layeredDraggableId);
                    layeredTarget = null;
                    baseDraggable.targetField.every(function(target) {
                        if (target.id === layeredTargetId) {
                            layeredTarget = target;
                        }

                        return true;
                    });

                    if ((layeredDraggable !== null) && (layeredTarget !== null)) {
                        layeredDraggable.moveDraggableTo('target', layeredTarget, function() {
                            processAnswerTargets(state, answerSortedByDepth, minDepth, maxDepth, depth, i + 1);
                        });
                    } else {
                        processAnswerTargets(state, answerSortedByDepth, minDepth, maxDepth, depth, i + 1);
                    }
                } else {
                    processAnswerTargets(state, answerSortedByDepth, minDepth, maxDepth, depth, i + 1);
                }
            }
        }

        function createBaseDraggableOnTarget(state, draggableId, targetId, reportError, funcCallback) {
            var draggable, target;

            if ((draggable = getById(state, 'draggables', draggableId)) === null) {
                if (reportError !== false) {
                    console.log(
                    'ERROR: In answer there exists a ' +
                    'draggable ID "' + draggableId + '". No ' +
                    'draggable with this ID could be found.'
                );
                }

                return false;
            }

            if ((target = getById(state, 'targets', targetId)) === null) {
                if (reportError !== false) {
                    console.log(
                    'ERROR: In answer there exists a target ' +
                    'ID "' + targetId + '". No target with this ' +
                    'ID could be found.'
                );
                }

                return false;
            }

            draggable.moveDraggableTo('target', target, funcCallback);

            return true;
        }

        function processAnswerPositions(state, answer) {
            var draggableId, draggable;

            (function(c1) {
                while (c1 < answer.length) {
                    for (draggableId in answer[c1]) {
                        if (answer[c1].hasOwnProperty(draggableId) === false) {
                            continue;
                        }

                        if ((draggable = getById(state, 'draggables', draggableId)) === null) {
                            console.log(
                            'ERROR: In answer there exists a ' +
                            'draggable ID "' + draggableId + '". No ' +
                            'draggable with this ID could be found.'
                        );

                            continue;
                        }

                        draggable.moveDraggableTo('XY', {
                            x: answer[c1][draggableId][0],
                            y: answer[c1][draggableId][1]
                        });
                    }

                    c1 += 1;
                }
            }(0));
        }

        function repositionDraggables(state, answer) {
            var answerSortedByDepth, minDepth, maxDepth;

            answerSortedByDepth = {};
            minDepth = 1000;
            maxDepth = 0;

            answer.every(function(chain) {
                var depth;

                depth = findDepth(chain, 0);

                if (depth < minDepth) {
                    minDepth = depth;
                }
                if (depth > maxDepth) {
                    maxDepth = depth;
                }

                if (answerSortedByDepth.hasOwnProperty(depth) === false) {
                    answerSortedByDepth[depth] = [];
                }

                answerSortedByDepth[depth].push(chain);

                return true;
            });

            if (answer.length === 0) {
                return;
            }

        // For now we support only one case.
            if ((minDepth < 1) || (maxDepth > 3)) {
                return;
            }

            if (state.config.individualTargets === true) {
                processAnswerTargets(state, answerSortedByDepth, minDepth, maxDepth, maxDepth, 0);
            } else if (state.config.individualTargets === false) {
                processAnswerPositions(state, answer);
            }
        }

        function findDepth(tempObj, depth) {
            var i;

            if ($.isPlainObject(tempObj) === false) {
                return depth;
            }

            depth += 1;

            for (i in tempObj) {
                if (tempObj.hasOwnProperty(i) === true) {
                    depth = findDepth(tempObj[i], depth);
                }
            }

            return depth;
        }

        function getById(state, type, id, fromTargetField, inContainer, targetId, baseDraggableId, baseTargetId) {
            return (function(c1) {
                while (c1 < state[type].length) {
                    if (type === 'draggables') {
                        if ((targetId !== undefined) && (inContainer === false) && (baseDraggableId !== undefined) && (baseTargetId !== undefined)) {
                            if (
                            (state[type][c1].id === id) &&
                            (state[type][c1].inContainer === false) &&
                            (state[type][c1].onTarget.id === targetId) &&
                            (state[type][c1].onTarget.type === 'on_drag') &&
                            (state[type][c1].onTarget.draggableObj.id === baseDraggableId) &&
                            (state[type][c1].onTarget.draggableObj.onTarget.id === baseTargetId)
                        ) {
                                return state[type][c1];
                            }
                        } else if ((targetId !== undefined) && (inContainer === false)) {
                            if (
                            (state[type][c1].id === id) &&
                            (state[type][c1].inContainer === false) &&
                            (state[type][c1].onTarget.id === targetId)
                        ) {
                                return state[type][c1];
                            }
                        } else {
                            if (inContainer === false) {
                                if ((state[type][c1].id === id) && (state[type][c1].inContainer === false)) {
                                    return state[type][c1];
                                }
                            } else {
                                if ((state[type][c1].id === id) && (state[type][c1].inContainer === true)) {
                                    return state[type][c1];
                                }
                            }
                        }
                    } else { // 'targets'
                        if (fromTargetField === true) {
                            if ((state[type][c1].id === id) && (state[type][c1].type === 'on_drag')) {
                                return state[type][c1];
                            }
                        } else {
                            if ((state[type][c1].id === id) && (state[type][c1].type === 'base')) {
                                return state[type][c1];
                            }
                        }
                    }

                    c1 += 1;
                }

                return null;
            }(0));
        }
    }); // End-of: define([], function () {
}(RequireJS.requirejs, RequireJS.require, RequireJS.define)); // End-of: (function (requirejs, require, define) {
