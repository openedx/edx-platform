(function (requirejs, require, define) {

// VideoSpeedControl module.
define(
'video/08_video_speed_control.js',
[],
function () {

    // VideoSpeedControl() function - what this module "exports".
    return function (state) {
        state.videoSpeedControl = {};

        if (state.videoType === 'html5') {
            _initialize(state);
        } else if (state.videoType === 'youtube' && state.youtubeXhr) {
            state.youtubeXhr.done(function () {
                _initialize(state);
            });
        }

        if (state.videoType === 'html5' && !(_checkPlaybackRates())) {
            console.log(
                '[Video info]: HTML5 mode - playbackRate is not supported.'
            );

            _hideSpeedControl(state);

            return;
        }
    };

    // ***************************************************************
    // Private functions start here.
    // ***************************************************************

    function _initialize(state) {
        _makeFunctionsPublic(state);
        _renderElements(state);
        _bindHandlers(state);
    }

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

        $.each(state.videoSpeedControl.speeds, function (index, speed) {
            var link = '<a class="speed_link" href="#">' + speed + 'x</a>';

            state.videoSpeedControl.videoSpeedsEl
                .prepend(
                    $('<li data-speed="' + speed + '">' + link + '</li>')
                );
        });

        state.videoSpeedControl.setSpeed(state.speed);

        // ARIA
        // Let screen readers know that:

        // this anchor behaves like a button
        state.videoSpeedControl.el.children('a').attr('role', gettext('button'));

        // what its name is: (title attribute is set in video.html template):
        state.videoSpeedControl.el.children('a').attr('aria-label', 'Speeds');
        
        // what its state is:
        state.videoSpeedControl.el.children('a').attr('aria-disabled', 'false');
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

        // If browser supports, 1.0 should be returned by playbackRate
        // property. In this case, function return True. Otherwise, False will
        // be returned.
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
            state.videoSpeedControl.el.on('click', function (event) {
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
            // The tabbing will cycle through the elements in the following
            // order:
            // 1. Play control
            // 2. Speed control
            // 3. Fastest speed called firstSpeed
            // 4. Intermediary speed called otherSpeed 
            // 5. Slowest speed called lastSpeed
            // 6. Volume control
            // This field will keep track of where the focus is coming from.
            state.previousFocus = '';

            // ******************************
            // Attach 'focus', and 'blur' events to the speed control which
            // either brings up the speed dialog with individual speed entries,
            // or closes it.
            state.videoSpeedControl.el.children('a')
                .on('focus', function () {
                    // If the focus is coming from the first speed entry 
                    // (tabbing backwards) or last speed entry (tabbing forward) 
                    // hide the speed entries dialog.
                    if (state.previousFocus === 'firstSpeed' ||
                        state.previousFocus === 'lastSpeed') {
                         state.videoSpeedControl.el.removeClass('open');
                    }
                })
                .on('blur', function () {
                    // When the focus leaves this element, the speed entries
                    // dialog will be shown.
                    
                    // If we are tabbing forward (previous focus is play
                    // control), we open the dialog and set focus on the first
                    // speed entry.
                    if (state.previousFocus === 'playPause') {
                        state.videoSpeedControl.el.addClass('open');
                        state.videoSpeedControl.videoSpeedsEl
                        .find('a.speed_link:first')
                        .focus();
                    }

                    // If we are tabbing backwards (previous focus is volume 
                    // control), we open the dialog and set focus on the 
                    // last speed entry.
                    if (state.previousFocus === 'volume') {
                        state.videoSpeedControl.el.addClass('open');
                        state.videoSpeedControl.videoSpeedsEl
                        .find('a.speed_link:last')
                        .focus();
                    }
                    
                });

            // ******************************
            // Attach 'blur' event to elements which represent individual speed
            // entries and use it to track the origin of the focus.
            speedLinks = state.videoSpeedControl.videoSpeedsEl
                .find('a.speed_link');

            speedLinks.first().on('blur', function () {
                // The previous focus is a speed entry (we are tabbing
                // backwards), the dialog will close, set focus on the speed
                // control and track the focus on first speed.
                if (state.previousFocus === 'otherSpeed') {
                    state.previousFocus = 'firstSpeed';
                    state.videoSpeedControl.el.children('a').focus();
                }    
            });

            // Track the focus on intermediary speeds.
            speedLinks
                .filter(function (index) {
                    return index === 1 || index === 2
                })
                .on('blur', function () {
                    state.previousFocus = 'otherSpeed';
                });

            speedLinks.last().on('blur', function () {
                // The previous focus is a speed entry (we are tabbing forward),
                // the dialog will close, set focus on the speed control and
                // track the focus on last speed.
                if (state.previousFocus === 'otherSpeed') {
                    state.previousFocus = 'lastSpeed';
                    state.videoSpeedControl.el.children('a').focus();
                }   
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
        // When a speed entry has been selected, we want the speed control to 
        // regain focus.
        parentEl.parent().siblings('a').focus();
    }

    function reRender(params) {
        var _this = this;

        this.videoSpeedControl.videoSpeedsEl.empty();
        this.videoSpeedControl.videoSpeedsEl.find('li').removeClass('active');
        this.videoSpeedControl.speeds = params.newSpeeds;

        $.each(this.videoSpeedControl.speeds, function (index, speed) {
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
