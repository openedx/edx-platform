// Wrapper for RequireJS. It will make the standard requirejs(), require(), and
// define() functions from Require JS available inside the anonymous function.
//
// See https://edx-wiki.atlassian.net/wiki/display/LMS/Integration+of+Require+JS+into+the+system
(function (requirejs, require, define) {

define(['logme'], function (logme) {
    return Scroller;

    function Scroller(state) {
        var parentEl, moveLeftEl, showEl, moveRightEl, showElLeftMargin;

        parentEl = $(
            '<div ' +
                'style=" ' +
                    'width: 665px; ' +
                    'height: 102px; ' +
                    'margin-left: auto; ' +
                    'margin-right: auto; ' +
                '" ' +
            '></div>'
        );

        moveLeftEl = $(
            '<div ' +
                'style=" ' +
                    'width: 40px; ' +
                    'height: 102px; ' +
                    'display: inline; ' +
                    'float: left; ' +
                '" ' +
            '>' +
                '<div ' +
                    'style=" ' +
                        'width: 38px; ' +
                        'height: 100px; '+

                        'border: 1px solid #CCC; ' +
                        'background-color: #EEE; ' +
                        'background-image: -webkit-linear-gradient(top, #EEE, #DDD); ' +
                        'background-image: -moz-linear-gradient(top, #EEE, #DDD); ' +
                        'background-image: -ms-linear-gradient(top, #EEE, #DDD); ' +
                        'background-image: -o-linear-gradient(top, #EEE, #DDD); ' +
                        'background-image: linear-gradient(top, #EEE, #DDD); ' +
                        '-webkit-box-shadow: 0 1px 0 rgba(255, 255, 255, 0.7) inset; ' +
                        'box-shadow: 0 1px 0 rgba(255, 255, 255, 0.7) inset; ' +

                        'background-image: url(\'/static/images/arrow-left.png\'); ' +
                        'background-position: center center; ' +
                        'background-repeat: no-repeat; ' +
                    '" ' +
                '></div>' +
            '</div>'
        );
        moveLeftEl.appendTo(parentEl);

        // The below is necessary to prevent the browser thinking that we want
        // to perform a drag operation, or a highlight operation. If we don't
        // do this, the browser will then highlight with a gray shade the
        // element.
        moveLeftEl.mousemove(function (event) { event.preventDefault(); });
        moveLeftEl.mousedown(function (event) { event.preventDefault(); });

        moveLeftEl.mouseup(function (event) {
            event.preventDefault();

            if (showElLeftMargin > -102) {
                return;
            }

            showElLeftMargin += 102;
            state.sliderEl.animate({
                'margin-left': showElLeftMargin + 'px'
            }, 100, function () {
                // Check if at the end, and make arrow less visibl.
                logme('showElLeftMargin = ' + showElLeftMargin);

                updateArrowOpacity();
            });
        });

        showEl = $(
            '<div ' +
                'style=" ' +
                    'width: 585px; ' +
                    'height: 102px; ' +
                    'overflow: hidden; ' +
                    'display: inline; ' +
                    'float: left; ' +
                '" ' +
            '></div>'
        );
        showEl.appendTo(parentEl);

        showElLeftMargin = 0;

        state.sliderEl = $(
            '<div ' +
                'style=" ' +
                    'width: 20000px; ' +
                    'height: 102px; ' +
                '" ' +
            '></div>'
        );
        state.sliderEl.appendTo(showEl);

        moveRightEl = $(
            '<div ' +
                'style=" ' +
                    'width: 40px; ' +
                    'height: 102px; ' +
                    'display: inline; ' +
                    'float: left; ' +
                '" ' +
            '>' +
                '<div ' +
                    'style=" ' +
                        'width: 38px; ' +
                        'height: 100px; '+

                        'border: 1px solid #CCC; ' +
                        'background-color: #EEE; ' +
                        'background-image: -webkit-linear-gradient(top, #EEE, #DDD); ' +
                        'background-image: -moz-linear-gradient(top, #EEE, #DDD); ' +
                        'background-image: -ms-linear-gradient(top, #EEE, #DDD); ' +
                        'background-image: -o-linear-gradient(top, #EEE, #DDD); ' +
                        'background-image: linear-gradient(top, #EEE, #DDD); ' +
                        '-webkit-box-shadow: 0 1px 0 rgba(255, 255, 255, 0.7) inset; ' +
                        'box-shadow: 0 1px 0 rgba(255, 255, 255, 0.7) inset; ' +

                        'background-image: url(\'/static/images/arrow-right.png\'); ' +
                        'background-position: center center; ' +
                        'background-repeat: no-repeat; ' +
                    '" ' +
                '></div>' +
            '</div>'
        );
        moveRightEl.appendTo(parentEl);

        // The below is necessary to prevent the browser thinking that we want
        // to perform a drag operation, or a highlight operation. If we don't
        // do this, the browser will then highlight with a gray shade the
        // element.
        moveRightEl.mousemove(function (event) { event.preventDefault(); });
        moveRightEl.mousedown(function (event) { event.preventDefault(); });

        moveRightEl.mouseup(function (event) {
            event.preventDefault();

            if (showElLeftMargin < -102 * (state.sliderEl.children().length - 6)) {
                return;
            }

            showElLeftMargin -= 102;

            state.sliderEl.animate({
                'margin-left': showElLeftMargin + 'px'
            }, 100, function () {
                // Check if at the end, and make arrow less visible.
                logme('showElLeftMargin = ' + showElLeftMargin);
                logme('-102 * (state.sliderEl.children().length - 6) = ' + (-102 * (state.sliderEl.children().length - 6)));

                updateArrowOpacity();
            });
        });

        parentEl.appendTo(state.containerEl);

        state.updateArrowOpacity = updateArrowOpacity;

        return;

        function updateArrowOpacity() {
            moveLeftEl.children('div').css('opacity', '1');
            moveRightEl.children('div').css('opacity', '1');

            if (showElLeftMargin < -102 * (state.sliderEl.children().length - 6)) {
                moveRightEl.children('div').css('opacity', '.4');
            }
            if (showElLeftMargin > -102) {
                moveLeftEl.children('div').css('opacity', '.4');
            }
        }
    } // End-of: function Scroller(state)
});

// End of wrapper for RequireJS. As you can see, we are passing
// namespaced Require JS variables to an anonymous function. Within
// it, you can use the standard requirejs(), require(), and define()
// functions as if they were in the global namespace.
}(RequireJS.requirejs, RequireJS.require, RequireJS.define)); // End-of: (function (requirejs, require, define)
