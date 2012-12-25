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
                processDraggable(state.config.draggable[i]);
                i += 1;
            }
        }(0));

        function processDraggable(obj) {
            var draggableContainerEl;

            logme(obj);

            draggableContainerEl = $(
                '<div ' +
                    'style=" ' +
                        'width: 100px; ' +
                        'height: 100px; ' +
                        'display: inline; ' +
                        'float: left; ' +
                    '" ' +
                    '></div>'
            );

            if (obj.icon.length > 0) {
                draggableContainerEl.append(
                    $('<img src="' + state.config.imageDir + '/' + obj.icon + '" />')
                );
            }

            draggableContainerEl.appendTo(state.sliderEl);
        }

    }
});

// End of wrapper for RequireJS. As you can see, we are passing
// namespaced Require JS variables to an anonymous function. Within
// it, you can use the standard requirejs(), require(), and define()
// functions as if they were in the global namespace.
}(RequireJS.requirejs, RequireJS.require, RequireJS.define)); // End-of: (function (requirejs, require, define)
