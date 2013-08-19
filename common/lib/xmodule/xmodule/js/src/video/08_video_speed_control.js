(function (requirejs, require, define) {

// VideoSpeedControl module.
define(
'video/08_video_speed_control.js',
[],
function () {

    // VideoSpeedControl() function - what this module "exports".
    return function (state) {
        state.videoSpeedControl = {};

        if (state.videoType === 'html5' && !(_checkPlaybackRates())) {
            _hideSpeedControl(state);

            return;
        }

        _makeFunctionsPublic(state);
        _renderElements(state);
        _bindHandlers(state);
    };

    // ***************************************************************
    // Private functions start here.
    // ***************************************************************

    // function _makeFunctionsPublic(state)
    //
    //     Functions which will be accessible via 'state' object. When called,
    //     these functions will get the 'state' object as a context.
    function _makeFunctionsPublic(state) {
        state.videoSpeedControl.changeVideoSpeed = _.bind(
            changeVideoSpeed, state
        );
        state.videoSpeedControl.setSpeed = _.bind(setSpeed, state);
        state.videoSpeedControl.reRender = _.bind(reRender, state);
    }

    // function _renderElements(state)
    //
    //     Create any necessary DOM elements, attach them, and set their
    //     initial configuration. Also make the created DOM elements available
    //     via the 'state' object. Much easier to work this way - you don't
    //     have to do repeated jQuery element selects.
    function _renderElements(state) {
        state.videoSpeedControl.speeds = state.speeds;

        state.videoSpeedControl.el = state.el.find('div.speeds');

        state.videoSpeedControl.videoSpeedsEl = state.videoSpeedControl.el
            .find('.video_speeds');

        state.videoControl.secondaryControlsEl.prepend(
            state.videoSpeedControl.el
        );

        $.each(state.videoSpeedControl.speeds, function(index, speed) {
            var link = '<a class="speed_link" href="#">' + speed + 'x</a>';

            state.videoSpeedControl.videoSpeedsEl
                .prepend(
                    $('<li data-speed="' + speed + '">' + link + '</li>')
                );
        });

        state.videoSpeedControl.setSpeed(state.speed);
    }

    /**
    * @desc Check if playbackRate supports by browser.
    *
    * @type {function}
    * @access private
    *
    * @param {object} state The object containg the state of the video player.
    *     All other modules, their parameters, public variables, etc. are
    *     available via this object.
    *
    * @this {object} The global window object.
    *
    * @returns {Boolean}
    *       true: Browser support playbackRate functionality.
    *       false: Browser doesn't support playbackRate functionality.
    */
    function _checkPlaybackRates() {
        var video = document.createElement('video');

        // If browser supports, 1.0 should be returned by playbackRate property.
        // In this case, function return True. Otherwise, False will be returned.
        return Boolean(video.playbackRate);
    }

    // Hide speed control.
    function _hideSpeedControl(state) {
        state.el.find('div.speeds').hide();
    }

    /**
     * @desc Bind any necessary function callbacks to DOM events (click,
     *     mousemove, etc.).
     *
     * @type {function}
     * @access private
     *
     * @param {object} state The object containg the state of the video player.
     *     All other modules, their parameters, public variables, etc. are
     *     available via this object.
     *
     * @this {object} The global window object.
     *
     * @returns {undefined}
     */
    function _bindHandlers(state) {
        var speedLinks;

        state.videoSpeedControl.videoSpeedsEl.find('a')
            .on('click', state.videoSpeedControl.changeVideoSpeed);

        if (onTouchBasedDevice()) {
            state.videoSpeedControl.el.on('click', function(event) {
                // So that you can't highlight this control via a drag
                // operation, we disable the default browser actions on a
                // click event.
                event.preventDefault();

                state.videoSpeedControl.el.toggleClass('open');
            });
        } else {
            state.videoSpeedControl.el
                .on('mouseenter', function () {
                    state.videoSpeedControl.el.addClass('open');
                })
                .on('mouseleave', function () {
                    state.videoSpeedControl.el.removeClass('open');
                })
                .on('click', function (event) {
                    // So that you can't highlight this control via a drag
                    // operation, we disable the default browser actions on a
                    // click event.
                    event.preventDefault();

                    state.videoSpeedControl.el.removeClass('open');
                });

            // ******************************
            // Attach 'focus', and 'blur' events to the speed button which
            // either brings up the speed dialog with individual speed entries,
            // or closes it.
            state.videoSpeedControl.el.children('a')
                .on('focus', function () {
                    // If the focus is comming from the first speed entry, this
                    // means we are tabbing backwards. In this case we have to
                    // hide the speed entries which will allow us to change the
                    // focus further backwards.
                    if (state.firstSpeedBlur === true) {
                        state.videoSpeedControl.el.removeClass('open');

                        state.firstSpeedBlur = false;
                    }

                    // If the focus is comming from some other element, show
                    // the drop down with the speed entries.
                    else {
                        state.videoSpeedControl.el.addClass('open');
                    }
                })
                .on('blur', function () {
                    // When the focus leaves this element, if the speed entries
                    // dialog is shown (tabbing forwards), then we will set
                    // focus to the first speed entry.
                    //
                    // If the selector does not select anything, then this
                    // means that the speed entries dialog is closed, and we
                    // are tabbing backwads. The browser will select the
                    // previous element to tab to by itself.
                    state.videoSpeedControl.videoSpeedsEl
                        .find('a.speed_link:first')
                        .focus();
                });


            // ******************************
            // Attach 'focus', and 'blur' events to elements which represent
            // individual speed entries.
            speedLinks = state.videoSpeedControl.videoSpeedsEl
                .find('a.speed_link');

            speedLinks.last().on('blur', function () {
                // If we have reached the last speed entry, and the focus
                // changes to the next element, we need to hide the speeds
                // control drop-down.
                state.videoSpeedControl.el.removeClass('open');
            });
            speedLinks.first().on('blur', function () {
                // This flag will indicate that the focus to the next
                // element that will receive it is comming from the first
                // speed entry.
                //
                // This flag will be used to correctly handle scenario of
                // tabbing backwards.
                state.firstSpeedBlur = true;
            });
            speedLinks.on('focus', function () {
                // Clear the flag which is only set when we are un-focusing
                // (the blur event) from the first speed entry.
                state.firstSpeedBlur = false;
            });
        }
    }

    // ***************************************************************
    // Public functions start here.
    // These are available via the 'state' object. Their context ('this'
    // keyword) is the 'state' object. The magic private function that makes
    // them available and sets up their context is makeFunctionsPublic().
    // ***************************************************************

    function setSpeed(speed) {
        this.videoSpeedControl.videoSpeedsEl.find('li').removeClass('active');
        this.videoSpeedControl.videoSpeedsEl
            .find("li[data-speed='" + speed + "']")
            .addClass('active');
        this.videoSpeedControl.el.find('p.active').html('' + speed + 'x');
    }

    function changeVideoSpeed(event) {
        var parentEl = $(event.target).parent();

        event.preventDefault();

        if (!parentEl.hasClass('active')) {
            this.videoSpeedControl.currentSpeed = parentEl.data('speed');

            this.videoSpeedControl.setSpeed(
                // To meet the API expected format.
                parseFloat(this.videoSpeedControl.currentSpeed)
                    .toFixed(2)
                    .replace(/\.00$/, '.0')
            );

            this.trigger(
                'videoPlayer.onSpeedChange',
                this.videoSpeedControl.currentSpeed
            );
        }
    }

    function reRender(params) {
        var _this = this;

        this.videoSpeedControl.videoSpeedsEl.empty();
        this.videoSpeedControl.videoSpeedsEl.find('li').removeClass('active');
        this.videoSpeedControl.speeds = params.newSpeeds;

        $.each(this.videoSpeedControl.speeds, function(index, speed) {
            var link, listItem;

            link = '<a class="speed_link" href="#">' + speed + 'x</a>';

            listItem = $('<li data-speed="' + speed + '">' + link + '</li>');

            if (speed === params.currentSpeed) {
                listItem.addClass('active');
            }

            _this.videoSpeedControl.videoSpeedsEl.prepend(listItem);
        });

        // Re-attach all events with their appropriate callbacks to the
        // newly generated elements.
        _bindHandlers(this);
    }

});

}(RequireJS.requirejs, RequireJS.require, RequireJS.define));
