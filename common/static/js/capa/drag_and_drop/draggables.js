// Wrapper for RequireJS. It will make the standard requirejs(), require(), and
// define() functions from Require JS available inside the anonymous function.
//
// See https://edx-wiki.atlassian.net/wiki/display/LMS/Integration+of+Require+JS+into+the+system
(function (requirejs, require, define) {

define(['logme'], function (logme) {
    return Draggables;

    function Draggables(state) {
        var _draggables;

        _draggables = [];

        (function (i) {
            while (i < state.config.draggable.length) {
                processDraggable(state.config.draggable[i], i + 1);
                i += 1;
            }
        }(0));

        return;

        function processDraggable(obj, index) {
            var draggableContainerEl, imgEl, inContainer, ousePressed;

            draggableContainerEl = $(
                '<div ' +
                    'style=" ' +
                        'width: 100px; ' +
                        'height: 100px; ' +
                        'display: inline; ' +
                        'float: left; ' +
                        'overflow: hidden; ' +
                        'z-index: ' + index + '; ' +
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

            draggableContainerEl.mousedown(mouseDown);
            draggableContainerEl.mouseup(mouseUp);
            draggableContainerEl.mousemove(mouseMove);
            draggableContainerEl.mouseleave(mouseLeave);

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

            function mouseUp(event) {
                if (mousePressed === true) {
                    checkLandingElement(event);
                }
            }

            function mouseMove(event) {
                if (mousePressed === true) {
                    draggableContainerEl.css('left', (event.pageX - 50));
                    draggableContainerEl.css('top', (event.pageY - 50));
                    event.preventDefault();
                }
            }

            function mouseLeave(event) {
                if (mousePressed === true) {
                    checkLandingElement(event);
                }
            }

            function checkLandingElement(event) {
                var offsetDE, offsetTE, indexes, DEindex;

                mousePressed = false;

                offsetDE = draggableContainerEl.offset();
                offsetTE = state.targetEl.offset();

                if (
                    (offsetDE.left < offsetTE.left) ||
                    (offsetDE.left + 100 > offsetTE.left + state.targetEl.width()) ||
                    (offsetDE.top < offsetTE.top) ||
                    (offsetDE.top + 100 > offsetTE.top + state.targetEl.height())
                ) {
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

                    (function (c1) {
                        while (c1 < indexes.length) {
                            if ((inContainer === false) && (indexes[c1].index > DEindex)) {
                                indexes[c1].el.before(draggableContainerEl);
                                inContainer = true;
                            }

                            c1 += 1;
                        }
                    }(0));

                    if (inContainer === false) {
                        draggableContainerEl.appendTo(state.sliderEl);
                        inContainer = true;
                    }
                }

                (function (c1) {
                    while (c1 < _draggables.length) {
                        if (parseInt(draggableContainerEl.attr('data-old-z-index'), 10) < parseInt(_draggables[c1].css('z-index'), 10)) {
                            _draggables[c1].css('z-index', parseInt(_draggables[c1].css('z-index'), 10) - 1);
                        }
                        c1 += 1;
                    }

                    draggableContainerEl.css('z-index', c1);
                }(0));

                event.preventDefault();
            }
        }

    }
});

// End of wrapper for RequireJS. As you can see, we are passing
// namespaced Require JS variables to an anonymous function. Within
// it, you can use the standard requirejs(), require(), and define()
// functions as if they were in the global namespace.
}(RequireJS.requirejs, RequireJS.require, RequireJS.define)); // End-of: (function (requirejs, require, define)
