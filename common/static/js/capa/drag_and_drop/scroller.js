(function (requirejs, require, define) {
define([], function () {
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

                        "background-image: url('"+baseUrl+"images/arrow-left.png'); " +
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

        // This event will be responsible for moving the scroller left.
        // Hidden draggables will be shown.
        moveLeftEl.mouseup(function (event) {
            event.preventDefault();

            // When there are no more hidden draggables, prevent from
            // scrolling infinitely.
            if (showElLeftMargin > -102) {
                return;
            }

            showElLeftMargin += 102;

            // We scroll by changing the 'margin-left' CSS property smoothly.
            state.sliderEl.animate({
                'margin-left': showElLeftMargin + 'px'
            }, 100, function () {
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

        // Element where the draggables will be contained. It is very long
        // so that any SANE number of draggables will fit in a single row. It
        // will be contained in a parent element whose 'overflow' CSS value
        // will be hidden, preventing the long row from fully being visible.
        state.sliderEl = $(
            '<div ' +
                'style=" ' +
                    'width: 20000px; ' +
                    'height: 100px; ' +
                    'border-top: 1px solid #CCC; ' +
                    'border-bottom: 1px solid #CCC; ' +
                '" ' +
            '></div>'
        );
        state.sliderEl.appendTo(showEl);

        state.sliderEl.mousedown(function (event) {
            event.preventDefault();
        });

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

                        "background-image: url('"+baseUrl+"images/arrow-right.png'); " +
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

        // This event will be responsible for moving the scroller right.
        // Hidden draggables will be shown.
        moveRightEl.mouseup(function (event) {
            event.preventDefault();

            // When there are no more hidden draggables, prevent from
            // scrolling infinitely.
            if (showElLeftMargin < -102 * (state.numDraggablesInSlider - 6)) {
                return;
            }

            showElLeftMargin -= 102;

            // We scroll by changing the 'margin-left' CSS property smoothly.
            state.sliderEl.animate({
                'margin-left': showElLeftMargin + 'px'
            }, 100, function () {
                updateArrowOpacity();
            });
        });

        parentEl.appendTo(state.containerEl);

        // Make the function available throughout the application. We need to
        // call it in several places:
        //
        // 1.) When initially reading answer from server, if draggables will be
        // positioned on the base image, the scroller's right and left arrows
        // opacity must be updated.
        //
        // 2.) When creating draggable elements, the scroller's right and left
        // arrows opacity must be updated according to the number of
        // draggables.
        state.updateArrowOpacity = updateArrowOpacity;

        return;

        function updateArrowOpacity() {
            moveLeftEl.children('div').css('opacity', '1');
            moveRightEl.children('div').css('opacity', '1');

            if (showElLeftMargin < -102 * (state.numDraggablesInSlider - 6)) {
                moveRightEl.children('div').css('opacity', '.4');
            }
            if (showElLeftMargin > -102) {
                moveLeftEl.children('div').css('opacity', '.4');
            }
        }
    } // End-of: function Scroller(state)
}); // End-of: define([], function () {
}(RequireJS.requirejs, RequireJS.require, RequireJS.define)); // End-of: (function (requirejs, require, define) {
