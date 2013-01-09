// Wrapper for RequireJS. It will make the standard requirejs(), require(), and
// define() functions from Require JS available inside the anonymous function.
//
// See https://edx-wiki.atlassian.net/wiki/display/LMS/Integration+of+Require+JS+into+the+system
(function (requirejs, require, define) {

define(['logme'], function (logme) {
    return Targets;

    function Targets(state) {
        var c1;

        state.targets = [];

        for (c1 = 0; c1 < state.config.targets.length; c1++) {
            processTarget(state.config.targets[c1]);
        }

        return;

        function processTarget(obj) {
            var targetEl, borderCss, numTextEl, targetObj;

            borderCss = '';
            if (state.config.targetOutline === true) {
                borderCss = 'border: 1px dashed gray; ';
            }

            targetEl = $(
                '<div ' +
                    'style=" ' +
                        'display: block; ' +
                        'position: absolute; ' +
                        'width: ' + obj.w + 'px; ' +
                        'height: ' + obj.h + 'px; ' +
                        'top: ' + obj.y + 'px; ' +
                        'left: ' + obj.x + 'px; ' +
                        borderCss +
                    '" ' +
                    'data-target-id="' + obj.id + '" ' +
                '></div>'
            );
            targetEl.appendTo(state.baseImageEl.parent());
            targetEl.mousedown(function (event) {
                event.preventDefault();
            });

            if (state.config.one_per_target === false) {
                numTextEl = $(
                    '<div ' +
                        'style=" ' +
                            'display: block; ' +
                            'position: absolute; ' +
                            'width: 24px; ' +
                            'height: 24px; ' +
                            'top: ' + obj.y + 'px; ' +
                            'left: ' + (obj.x + obj.w - 24) + 'px; ' +
                            'border: 1px solid black; ' +
                            'text-align: center; ' +
                            'z-index: 500; ' +
                            'background-color: white; ' +
                            'font-size: 0.95em; ' +
                            'color: #009fe2; ' +
                            'cursor: pointer; ' +
                        '" ' +
                    '>0</div>'
                );
            } else {
                numTextEl = null;
            }

            targetObj = {
                'id': obj.id,

                'w': obj.w,
                'h': obj.h,

                'el': targetEl,
                'offset': targetEl.position(),

                'draggable': [],

                'targetEl': targetEl,

                'numTextEl': numTextEl,
                'updateNumTextEl': updateNumTextEl
            };

            if (state.config.one_per_target === false) {
                numTextEl.appendTo(state.baseImageEl.parent());
                numTextEl.mousedown(function (event) {
                    event.preventDefault();
                });
                numTextEl.mouseup(function () {
                    cycleDraggableOrder.call(targetObj)
                });
            }

            state.targets.push(targetObj);
        }

        function cycleDraggableOrder() {
            var draggablesInMe, c1, c2, lowestZIndex, highestZIndex;

            if (this.draggable.length === 0) {
                return 0;
            }

            draggablesInMe = [];

            for (c1 = 0; c1 < this.draggable.length; c1 += 1) {
                for (c2 = 0; c2 < state.draggables.length; c2 += 1) {
                    if (this.draggable[c1] === state.draggables[c2].id) {
                        draggablesInMe.push(state.draggables[c2]);
                    }
                }
            }

            highestZIndex = -10000;
            lowestZIndex = 10000;

            for (c1 = 0; c1 < draggablesInMe.length; c1 += 1) {
                logme(
                    'draggablesInMe[' + c1 + '].id = ' + draggablesInMe[c1].id,
                    'draggablesInMe[' + c1 + '].zIndex = ' + draggablesInMe[c1].zIndex,
                    'draggablesInMe[' + c1 + '].oldZIndex = ' + draggablesInMe[c1].oldZIndex
                );
            }
            logme('------------------');

            for (c1 = 0; c1 < draggablesInMe.length; c1 += 1) {
                if (draggablesInMe[c1].zIndex < lowestZIndex) {
                    lowestZIndex = draggablesInMe[c1].zIndex;
                }

                if (draggablesInMe[c1].zIndex > highestZIndex) {
                    highestZIndex = draggablesInMe[c1].zIndex;
                }
            }

            for (c1 = 0; c1 < draggablesInMe.length; c1 += 1) {
                if (draggablesInMe[c1].zIndex === lowestZIndex) {
                    draggablesInMe[c1].zIndex = highestZIndex;
                    draggablesInMe[c1].oldZIndex = highestZIndex;
                } else {
                    draggablesInMe[c1].zIndex -= 1;
                    draggablesInMe[c1].oldZIndex -= 1;
                }

                draggablesInMe[c1].iconEl.css('z-index', draggablesInMe[c1].zIndex);
                if (draggablesInMe[c1].labelEl !== null) {
                    draggablesInMe[c1].labelEl.css('z-index', draggablesInMe[c1].zIndex);
                }
            }
        }
    } // function Targets(state) {

    function updateNumTextEl() {
        this.numTextEl.html(this.draggable.length);
    }
});

// End of wrapper for RequireJS. As you can see, we are passing
// namespaced Require JS variables to an anonymous function. Within
// it, you can use the standard requirejs(), require(), and define()
// functions as if they were in the global namespace.
}(RequireJS.requirejs, RequireJS.require, RequireJS.define)); // End-of: (function (requirejs, require, define)
