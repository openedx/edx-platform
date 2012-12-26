// Wrapper for RequireJS. It will make the standard requirejs(), require(), and
// define() functions from Require JS available inside the anonymous function.
//
// See https://edx-wiki.atlassian.net/wiki/display/LMS/Integration+of+Require+JS+into+the+system
(function (requirejs, require, define) {

define(['logme', 'update_input'], function (logme, updateInput) {
    return Draggables;

    function Draggables(state) {
        var _draggables;

        _draggables = [];
        state.draggables = [];

        (function (i) {
            while (i < state.config.draggable.length) {
                processDraggable(state.config.draggable[i], i + 1);
                i += 1;
            }
        }(0));

        return;

        function processDraggable(obj, index) {
            var draggableContainerEl, imgEl, inContainer, ousePressed,
                onTarget, draggableObj;

            draggableContainerEl = $(
                '<div ' +
                    'style=" ' +
                        'width: 100px; ' +
                        'height: 100px; ' +
                        'display: inline; ' +
                        'float: left; ' +
                        'overflow: hidden; ' +
                        'z-index: ' + index + '; ' +
                        'border: 1px solid gray; ' +
                    '" ' +
                    'data-draggable-position-index="' + index + '" ' +
                    '></div>'
            );

            if (obj.icon.length > 0) {
                imgEl = $(
                    '<img ' +
                        'src="' + state.config.imageDir + '/' + obj.icon + '" ' +
                    '/>'
                );

                draggableContainerEl.append(imgEl);
            }

            if (obj.label.length > 0) {
                draggableContainerEl.append(
                    $('<div style="clear: both; text-align: center;">' + obj.label + '</div>')
                );
            }

            draggableContainerEl.appendTo(state.sliderEl);
            _draggables.push(draggableContainerEl);

            inContainer = true;
            mousePressed = false;

            onTarget = null;

            draggableObj = {
                'id': obj.id,
                'x': -1,
                'y': -1
            };
            state.draggables.push(draggableObj);

            draggableContainerEl.mousedown(mouseDown);
            draggableContainerEl.mouseup(mouseUp);
            draggableContainerEl.mousemove(mouseMove);
            draggableContainerEl.mouseleave(mouseLeave);

            if (state.individualTargets === false) {
                updateInput(state);
            }

            return;

            function mouseDown(event) {
                if (mousePressed === false) {
                    if (inContainer === true) {
                        draggableContainerEl.detach();
                        draggableContainerEl.css('position', 'absolute');
                        draggableContainerEl.css('left', event.pageX - 50);
                        draggableContainerEl.css('top', event.pageY - 50);
                        draggableContainerEl.appendTo(state.containerEl);

                        inContainer = false;
                    }

                    draggableContainerEl.attr('data-old-z-index', draggableContainerEl.css('z-index'));
                    draggableContainerEl.css('z-index', '1000');

                    mousePressed = true;
                    event.preventDefault();
                }
            }

            function mouseUp() {
                if (mousePressed === true) {
                    checkLandingElement();
                }
            }

            function mouseMove() {
                if (mousePressed === true) {
                    draggableContainerEl.css('left', (event.pageX - 50));
                    draggableContainerEl.css('top', (event.pageY - 50));
                }
            }

            function mouseLeave() {
                if (mousePressed === true) {
                    checkLandingElement();
                }
            }

            function checkLandingElement() {
                var offsetDE, offsetTE, indexes, DEindex, targetFound;

                mousePressed = false;

                offsetDE = draggableContainerEl.offset();

                if (state.individualTargets === false) {
                    offsetTE = state.targetEl.offset();

                    if (
                        (offsetDE.left < offsetTE.left) ||
                        (offsetDE.left + 100 > offsetTE.left + state.targetEl.width()) ||
                        (offsetDE.top < offsetTE.top) ||
                        (offsetDE.top + 100 > offsetTE.top + state.targetEl.height())
                    ) {
                        moveBackToSlider();

                        draggableObj.x = -1;
                        draggableObj.y = -1;
                    } else {
                        correctZIndexes();

                        draggableObj.x = offsetDE.left + 50 - offsetTE.left;
                        draggableObj.y = offsetDE.top + 50 - offsetTE.top;
                    }
                } else if (state.individualTargets === true) {
                    targetFound = false;

                    checkIfOnTarget();

                    if (targetFound === true) {
                        correctZIndexes();
                    } else {
                        moveBackToSlider();
                        removeObjIdFromTarget();
                    }
                }

                updateInput(state);

                return;

                function removeObjIdFromTarget() {
                    var c1;

                    if (onTarget !== null) {
                        c1 = 0;

                        while (c1 < onTarget.draggable.length) {
                            if (onTarget.draggable[c1] === obj.id) {
                                onTarget.draggable.splice(c1, 1);

                                break;
                            }
                            c1 += 1;
                        }

                        onTarget = null;
                    }
                }

                function checkIfOnTarget() {
                    var c1, c2, target;

                    c1 = 0;

                    while (c1 < state.targets.length) {
                        target = state.targets[c1];

                        if (offsetDE.top + 50 < target.offset.top) {
                            c1 += 1;
                            continue;
                        }
                        if (offsetDE.top + 50 > target.offset.top + target.h) {
                            c1 += 1;
                            continue;
                        }
                        if (offsetDE.left + 50 < target.offset.left) {
                            c1 += 1;
                            continue;
                        }
                        if (offsetDE.left + 50 > target.offset.left + target.w) {
                            c1 += 1;
                            continue;
                        }

                        if (state.config.one_per_target === true) {
                            if (
                                (target.draggable.length === 1) &&
                                (target.draggable[0] !== obj.id)
                            ) {
                                c1 += 1;
                                continue;
                            }
                        }

                        targetFound = true;

                        removeObjIdFromTarget();
                        onTarget = target;

                        target.draggable.push(obj.id);
                        snapToTarget(target);

                        break;
                    }
                }

                function snapToTarget(target) {
                    draggableContainerEl.css('left', (target.offset.left + 0.5 * target.w - 50));
                    draggableContainerEl.css('top', (target.offset.top + 0.5 * target.h - 50));
                }

                function correctZIndexes() {
                    var c1;

                    c1 = 0;

                    while (c1 < _draggables.length) {
                        if (parseInt(draggableContainerEl.attr('data-old-z-index'), 10) < parseInt(_draggables[c1].css('z-index'), 10)) {
                            _draggables[c1].css('z-index', parseInt(_draggables[c1].css('z-index'), 10) - 1);
                        }
                        c1 += 1;
                    }

                    draggableContainerEl.css('z-index', c1);
                }

                function moveBackToSlider() {
                    var c1;

                    draggableContainerEl.detach();
                    draggableContainerEl.css('position', 'static');

                    indexes = [];
                    DEindex = parseInt(draggableContainerEl.attr('data-draggable-position-index'), 10);

                    state.sliderEl.children().each(function (index, value) {
                        indexes.push({
                            'index': parseInt($(value).attr('data-draggable-position-index'), 10),
                            'el': $(value)
                        });
                    });

                    c1 = 0;

                    while (c1 < indexes.length) {
                        if ((inContainer === false) && (indexes[c1].index > DEindex)) {
                            indexes[c1].el.before(draggableContainerEl);
                            inContainer = true;
                        }

                        c1 += 1;
                    }

                    if (inContainer === false) {
                        draggableContainerEl.appendTo(state.sliderEl);
                        inContainer = true;
                    }
                }
            }
        }

    }
});

// End of wrapper for RequireJS. As you can see, we are passing
// namespaced Require JS variables to an anonymous function. Within
// it, you can use the standard requirejs(), require(), and define()
// functions as if they were in the global namespace.
}(RequireJS.requirejs, RequireJS.require, RequireJS.define)); // End-of: (function (requirejs, require, define)
