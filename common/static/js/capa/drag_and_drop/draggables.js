// Wrapper for RequireJS. It will make the standard requirejs(), require(), and
// define() functions from Require JS available inside the anonymous function.
//
// See https://edx-wiki.atlassian.net/wiki/display/LMS/Integration+of+Require+JS+into+the+system
(function (requirejs, require, define) {

define(['logme'], function (logme) {
    return Draggables;

    function Draggables(state) {
        (function (i) {
            while (i < state.config.draggable.length) {
                processDraggable(state.config.draggable[i], i + 1);
                i += 1;
            }
        }(0));

        function processDraggable(obj, index) {
            var draggableContainerEl, imgEl, inContainer,
                mouseDown;

            draggableContainerEl = $(
                '<div ' +
                    'style=" ' +
                        'width: 100px; ' +
                        'height: 100px; ' +
                        'display: inline; ' +
                        'float: left; ' +
                        'overflow: hidden; ' +
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

            inContainer = true;
            mouseDown = false;

            draggableContainerEl.mousedown(function (event) {
                if (mouseDown === false) {
                    if (inContainer === true) {
                        draggableContainerEl.detach();
                        draggableContainerEl.css('position', 'absolute');
                        draggableContainerEl.css('left', (event.pageX - 50));
                        draggableContainerEl.css('top', (event.pageY - 50));
                        draggableContainerEl.appendTo(state.containerEl);

                        inContainer = false;
                    }

                    mouseDown = true;
                    event.preventDefault();
                }
            });

            draggableContainerEl.mouseup(function (event) {
                if (mouseDown === true) {
                    mouseDown = false;
                    checkLandingElement(event);
                    event.preventDefault();
                }
            });

            draggableContainerEl.mousemove(function (event) {
                if (mouseDown === true) {
                    draggableContainerEl.css('left', (event.pageX - 50));
                    draggableContainerEl.css('top', (event.pageY - 50));
                    event.preventDefault();
                }
            });

            draggableContainerEl.mouseleave(function (event) {
                if (mouseDown === true) {
                    mouseDown = false;
                    checkLandingElement(event);
                    event.preventDefault();
                }
            });

            return;

            function checkLandingElement(event) {
                var offsetDE, children;

                offsetDE = draggableContainerEl.offset();

                if (
                    (offsetDE.left < state.targetEl.offset().left) ||
                    (offsetDE.left + 100 > state.targetEl.offset().left + state.targetEl.width()) ||
                    (offsetDE.top < state.targetEl.offset().top) ||
                    (offsetDE.top + 100 > state.targetEl.offset().top + state.targetEl.height())
                ) {
                    draggableContainerEl.detach();
                    draggableContainerEl.css('position', 'static');

                    children = state.sliderEl.children();

                    if (children.length === 0) {
                        draggableContainerEl.appendTo(state.sliderEl);
                    } else {
                        state.sliderEl.children().each(function (index, value) {
                            if (inContainer === false) {
                                if (parseInt($(value).attr('data-draggable-position-index'), 10) + 1 === parseInt(draggableContainerEl.attr('data-draggable-position-index'), 10)) {
                                    $(value).after(draggableContainerEl);
                                    inContainer = true;
                                } else if (parseInt($(value).attr('data-draggable-position-index'), 10) - 1 === parseInt(draggableContainerEl.attr('data-draggable-position-index'), 10)) {
                                    $(value).before(draggableContainerEl);
                                    inContainer = true;
                                }
                            }
                        });
                    }

                    if (inContainer === false) {
                        draggableContainerEl.appendTo(state.sliderEl);
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
