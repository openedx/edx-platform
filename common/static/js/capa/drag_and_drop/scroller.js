// Wrapper for RequireJS. It will make the standard requirejs(), require(), and
// define() functions from Require JS available inside the anonymous function.
//
// See https://edx-wiki.atlassian.net/wiki/display/LMS/Integration+of+Require+JS+into+the+system
(function (requirejs, require, define) {

define(['logme'], function (logme) {
    return Scroller;

    function Scroller(state) {
        var parentEl, moveLeftEl, showEl, moveRightEL,
            moveRightEl_leftMargin;

        parentEl = $(
            '<div ' +
                'style=" ' +
                    'width: 95%; ' +
                    'height: 100px; ' +
                    'border: 1px solid black; ' +
                    'margin-left: auto; ' +
                    'margin-right: auto; ' +
                '" ' +
            '></div>'
        );

        moveLeftEl = $(
            '<div ' +
                'style=" ' +
                    'width: 6%; ' +
                    'height: 100px; ' +
                    'display: inline; ' +
                    'float: left; ' +
                    'background: url(\'/static/images/arrow-left.png\') center center no-repeat; ' +
                '" ' +
            '></div>'
        );
        moveLeftEl.appendTo(parentEl);

        moveLeftEl.click(function () {
            state.showElLeftMargin += 100;
            state.sliderEl.animate({
                'margin-left': state.showElLeftMargin + 'px'
            });
        });

        showEl = $(
            '<div ' +
                'style=" ' +
                    'width: 88%; ' +
                    'height: 100px; ' +
                    'overflow: hidden; ' +
                    'display: inline; ' +
                    'float: left; ' +
                '" ' +
            '></div>'
        );
        showEl.appendTo(parentEl);

        state.showElLeftMargin = 0;

        state.sliderEl = $(
            '<div ' +
                'style=" ' +
                    'width: 800px; ' +
                    'height: 100px; ' +
                '" ' +
            '></div>'
        );
        state.sliderEl.appendTo(showEl);

        moveRightEl = $(
            '<div ' +
                'style=" ' +
                    'width: 6%; ' +
                    'height: 100px; ' +
                    'display: inline; ' +
                    'float: left; ' +
                    'background: url(\'/static/images/arrow-right.png\') center center no-repeat; ' +
                '" ' +
            '></div>'
        );
        moveRightEl.appendTo(parentEl);

        moveRightEl.click(function () {
            state.showElLeftMargin -= 100;
            state.sliderEl.animate({
                'margin-left': state.showElLeftMargin + 'px'
            });
        });

        parentEl.appendTo(state.containerEl);
    }
});

// End of wrapper for RequireJS. As you can see, we are passing
// namespaced Require JS variables to an anonymous function. Within
// it, you can use the standard requirejs(), require(), and define()
// functions as if they were in the global namespace.
}(RequireJS.requirejs, RequireJS.require, RequireJS.define)); // End-of: (function (requirejs, require, define)
