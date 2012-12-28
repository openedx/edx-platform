// Wrapper for RequireJS. It will make the standard requirejs(), require(), and
// define() functions from Require JS available inside the anonymous function.
//
// See https://edx-wiki.atlassian.net/wiki/display/LMS/Integration+of+Require+JS+into+the+system
(function (requirejs, require, define) {

define(['logme', 'update_input'], function (logme, updateInput) {
    return Draggables;

    function Draggables(state) {
        var c1;

        state.draggables = [];

        for (c1 = 0; c1 < state.config.draggables.length; c1 += 1) {
            processDraggable(state.config.draggables[c1], c1 + 1);
        }

        state.currentMovingDraggable = null;

        $(document).mousemove(function (event) {
            normalizeEvent(event);

            if (state.currentMovingDraggable !== null) {
                state.currentMovingDraggable.css('left', event.pageX - state.baseImageEl.offset().left - 50);
                state.currentMovingDraggable.css('top', event.pageY - state.baseImageEl.offset().top - 50);
            }
        });

        return;

        function processDraggable(obj, objIndex) {
            var draggableContainerEl, inContainer, mousePressed, onTarget,
                draggableObj, marginCss;

            draggableContainerEl = $(
                '<div ' +
                    'style=" ' +
                        'width: 100px; ' +
                        'height: 100px; ' +
                        'display: inline; ' +
                        'float: left; ' +
                        'overflow: hidden; ' +
                        'z-index: ' + objIndex + '; ' +
                        'border: 1px solid #CCC; ' +
                        'text-align: center; ' +
                    '" ' +
                    'data-draggable-position-index="' + objIndex + '" ' +
                    '></div>'
            );

            if (obj.icon.length > 0) {
                draggableContainerEl.append(
                    $('<img src="' + state.config.imageDir + '/' + obj.icon + '" />')
                );
            }

            if (obj.label.length > 0) {
                marginCss = '';

                if (obj.icon.length === 0) {
                    marginCss = 'margin-top: 38px;';
                }

                draggableContainerEl.append(
                    $('<div style="clear: both; text-align: center; ' + marginCss + ' ">' + obj.label + '</div>')
                );
            }

            draggableContainerEl.appendTo(state.sliderEl);

            inContainer = true;
            mousePressed = false;

            onTarget = null;

            draggableObj = {
                'id': obj.id,
                'el': draggableContainerEl,
                'x': -1,
                'y': -1,

                'setInContainer': function (val) { inContainer = val; },
                'setOnTarget': function (val) { onTarget = val; },
            };
            state.draggables.push(draggableObj);

            draggableContainerEl.mousedown(mouseDown);
            draggableContainerEl.mouseup(mouseUp);
            draggableContainerEl.mousemove(mouseMove);

            return;

            function mouseDown(event) {
                if (mousePressed === false) {
                    state.currentMovingDraggable = draggableContainerEl;
                    normalizeEvent(event);

                    if (inContainer === true) {
                        draggableContainerEl.detach();
                        draggableContainerEl.css('border', 'none');
                        draggableContainerEl.css('position', 'absolute');
                        draggableContainerEl.css('left', event.pageX - state.baseImageEl.offset().left - 50);
                        draggableContainerEl.css('top', event.pageY - state.baseImageEl.offset().top - 50);
                        draggableContainerEl.appendTo(state.baseImageEl.parent());

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
                    state.currentMovingDraggable = null;

                    checkLandingElement(event);
                }
            }

            function mouseMove() {
                if (mousePressed === true) {
                    draggableContainerEl.css('left', event.pageX - state.baseImageEl.offset().left - 50);
                    draggableContainerEl.css('top', event.pageY - state.baseImageEl.offset().top - 50);
                }
            }

            // At this point the mouse was realeased, and we need to check
            // where the draggable eneded up. Based on several things, we
            // will either move the draggable back to the slider, or update
            // the input with the user's answer (X-Y position of the draggable,
            // or the ID of the target where it landed.
            function checkLandingElement() {
                var offsetDE, indexes, DEindex, targetFound;

                mousePressed = false;

                offsetDE = draggableContainerEl.position();

                if (state.individualTargets === true) {
                    targetFound = false;

                    checkIfOnTarget();

                    if (targetFound === true) {
                        correctZIndexes();
                    } else {
                        moveBackToSlider();
                        removeObjIdFromTarget();
                    }
                } else {
                    if (
                        (offsetDE.left < 0) ||
                        (offsetDE.left + 100 > state.baseImageEl.width()) ||
                        (offsetDE.top < 0) ||
                        (offsetDE.top + 100 > state.baseImageEl.height())
                    ) {
                        moveBackToSlider();

                        draggableObj.x = -1;
                        draggableObj.y = -1;
                    } else {
                        correctZIndexes();

                        draggableObj.x = offsetDE.left + 50;
                        draggableObj.y = offsetDE.top + 50;
                    }
                }

                state.updateArrowOpacity();
                updateInput(state);

                return;

                function removeObjIdFromTarget() {
                    var c1;

                    if (onTarget !== null) {
                        for (c1 = 0; c1 < onTarget.draggable.length; c1 += 1) {
                            if (onTarget.draggable[c1] === obj.id) {
                                onTarget.draggable.splice(c1, 1);

                                break;
                            }
                        }

                        onTarget = null;
                    }
                }

                // Determine if a draggable, after it was relased, ends up on a
                // target. We do this by iterating over all of the targets, and
                // for each one we check whether the draggable's center is
                // within the target's dimensions.
                function checkIfOnTarget() {
                    var c1, target;

                    for (c1 = 0; c1 < state.targets.length; c1 += 1) {
                        target = state.targets[c1];

                        if (offsetDE.top + 50 < target.offset.top) {
                            continue;
                        }
                        if (offsetDE.top + 50 > target.offset.top + target.h) {
                            continue;
                        }
                        if (offsetDE.left + 50 < target.offset.left) {
                            continue;
                        }
                        if (offsetDE.left + 50 > target.offset.left + target.w) {
                            continue;
                        }

                        if (
                            (state.config.one_per_target === true) &&
                            (target.draggable.length === 1) &&
                            (target.draggable[0] !== obj.id)
                        ) {
                            continue;
                        }

                        targetFound = true;

                        // If the draggable was moved from one target to
                        // another, then we need to remove it's ID from the
                        // previous target's draggables list, and add it to the
                        // new target's draggables list.
                        if ((onTarget !== null) && (onTarget.id !== target.id)) {
                            removeObjIdFromTarget();
                            onTarget = target;
                            target.draggable.push(obj.id);
                        } else if (onTarget === null) {
                            onTarget = target;
                            target.draggable.push(obj.id);
                        }

                        // Reposition the draggable so that it's center
                        // coincides with the center of the target.
                        snapToTarget(target);

                        break;
                    }
                }

                function snapToTarget(target) {
                    draggableContainerEl.css('left', target.offset.left + 0.5 * target.w - 50);
                    draggableContainerEl.css('top', target.offset.top + 0.5 * target.h - 50);
                }

                // Go through all of the draggables subtract 1 from the z-index
                // of all whose z-index is higher than the old z-index of the
                // current element. After, set the z-index of the current
                // element to 1 + N (where N is the number of draggables - i.e.
                // the highest z-index possible).
                //
                // This will make sure that after releasing a draggable, it
                // will be on top of all of the other draggables. Also, the
                // ordering of the visibility (z-index) of the other draggables
                // will not change.
                function correctZIndexes() {
                    var c1;

                    for (c1 = 0; c1 < state.draggables.length; c1++) {
                        if (
                            parseInt(draggableContainerEl.attr('data-old-z-index'), 10) <
                            parseInt(state.draggables[c1].el.css('z-index'), 10)
                        ) {
                            state.draggables[c1].el.css(
                                'z-index',
                                parseInt(state.draggables[c1].el.css('z-index'), 10) - 1
                            );
                        }
                    }

                    draggableContainerEl.css('z-index', c1);
                }

                // If a draggable was released in a wrong positione, we will
                // move it back to the slider, placing it in the same position
                // that it was dragged out of.
                function moveBackToSlider() {
                    var c1;

                    draggableContainerEl.detach();
                    draggableContainerEl.css('position', 'static');

                    // Get the position indexes of all draggables that are
                    // currently in the slider, along with the corresponding
                    // jQuery element.
                    indexes = [];
                    state.sliderEl.children().each(function (index, value) {
                        indexes.push({
                            'index': parseInt($(value).attr('data-draggable-position-index'), 10),
                            'el': $(value)
                        });
                    });

                    // Get the position index of the element that we are
                    // inserting back into the slider.
                    DEindex = parseInt(draggableContainerEl.attr('data-draggable-position-index'), 10);

                    // Starting from the first position index that we
                    // retrieved, and going up, if we find a position index
                    // that is more than 'DEindex', we know that we must insert
                    // the current element before the element with the greater
                    // position index.
                    for (c1 = 0; c1 < indexes.length; c1 += 1) {
                        if ((inContainer === false) && (indexes[c1].index > DEindex)) {
                            indexes[c1].el.before(draggableContainerEl);
                            inContainer = true;
                        }
                    }

                    // If we did not find a greater postion index, then either
                    // there are no elements in the slider, or all of them
                    // have a lesser position index. In both cases we add the
                    // current draggable to the end.
                    if (inContainer === false) {
                        draggableContainerEl.appendTo(state.sliderEl);
                    }

                    inContainer = true;

                    draggableContainerEl.css('border', '1px solid gray');
                }
            }
        }

        // In firefox the event does not have a proper pageX and pageY
        // coordinates.
        function normalizeEvent(event) {
            if(!event.offsetX) {
                event.offsetX = (event.pageX - $(event.target).offset().left);
                event.offsetY = (event.pageY - $(event.target).offset().top);
            }
            return event;
        }
    }
});

// End of wrapper for RequireJS. As you can see, we are passing
// namespaced Require JS variables to an anonymous function. Within
// it, you can use the standard requirejs(), require(), and define()
// functions as if they were in the global namespace.
}(RequireJS.requirejs, RequireJS.require, RequireJS.define)); // End-of: (function (requirejs, require, define)
