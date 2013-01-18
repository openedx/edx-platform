// Wrapper for RequireJS. It will make the standard requirejs(), require(), and
// define() functions from Require JS available inside the anonymous function.
//
// See https://edx-wiki.atlassian.net/wiki/display/LMS/Integration+of+Require+JS+into+the+system
(function (requirejs, require, define) {

define(['logme'], function (logme) {
    return Targets;

    function Targets(state) {
        (function (c1) {
            while (c1 < state.config.targets.length) {
                processTarget(state, state.config.targets[c1]);

                c1 += 1;
            }
        }(0));
    }

    function processTarget(state, obj) {
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
            '></div>'
        );
        targetEl.appendTo(state.baseImageEl.parent());
        targetEl.mousedown(function (event) {
            event.preventDefault();
        });

        if (state.config.onePerTarget === false) {
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

            'draggableList': [],

            'state': state,

            'targetEl': targetEl,

            'numTextEl': numTextEl,
            'updateNumTextEl': updateNumTextEl,

            'removeDraggable': removeDraggable,
            'addDraggable': addDraggable
        };

        if (state.config.onePerTarget === false) {
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

    function removeDraggable(draggable) {
        var c1;

        this.draggableList.splice(draggable.onTargetIndex, 1);

        // An item from the array was removed. We need to updated all indexes accordingly.
        // Shift all indexes down by one if they are higher than the index of the removed item.
        c1 = 0;
        while (c1 < this.draggableList.length) {
            if (this.draggableList[c1].onTargetIndex > draggable.onTargetIndex) {
                this.draggableList[c1].onTargetIndex -= 1;
            }

            c1 += 1;
        }

        draggable.onTarget = null;
        draggable.onTargetIndex = null;

        this.updateNumTextEl();
    }

    function addDraggable(draggable) {
        draggable.onTarget = this;
        draggable.onTargetIndex = this.draggableList.push(draggable) - 1;

        this.updateNumTextEl();
    }

    /*
     * function cycleDraggableOrder
     *
     * Parameters:
     *     none - This function does not expect any parameters.
     *
     * Returns:
     *     undefined - The return value of this function is not used.
     *
     * Description:
     *     Go through all draggables that are on the current target, and decrease their
     *     z-index by 1, making sure that the bottom-most draggable ends up on the top.
     */
    function cycleDraggableOrder() {
        var c1, lowestZIndex, highestZIndex;

        if (this.draggableList.length < 2) {
            return;
        }

        highestZIndex = -10000;
        lowestZIndex = 10000;

        for (c1 = 0; c1 < this.draggableList.length; c1 += 1) {
            if (this.draggableList[c1].zIndex < lowestZIndex) {
                lowestZIndex = this.draggableList[c1].zIndex;
            }

            if (this.draggableList[c1].zIndex > highestZIndex) {
                highestZIndex = this.draggableList[c1].zIndex;
            }
        }

        for (c1 = 0; c1 < this.draggableList.length; c1 += 1) {
            if (this.draggableList[c1].zIndex === lowestZIndex) {
                this.draggableList[c1].zIndex = highestZIndex;
            } else {
                this.draggableList[c1].zIndex -= 1;
            }

            this.draggableList[c1].iconEl.css('z-index', this.draggableList[c1].zIndex);
            if (this.draggableList[c1].labelEl !== null) {
                this.draggableList[c1].labelEl.css('z-index', this.draggableList[c1].zIndex);
            }
        }
    }

    function updateNumTextEl() {
        if (this.numTextEl !== null) {
            this.numTextEl.html(this.draggableList.length);
        }
    }
});

// End of wrapper for RequireJS. As you can see, we are passing
// namespaced Require JS variables to an anonymous function. Within
// it, you can use the standard requirejs(), require(), and define()
// functions as if they were in the global namespace.
}(RequireJS.requirejs, RequireJS.require, RequireJS.define)); // End-of: (function (requirejs, require, define)
