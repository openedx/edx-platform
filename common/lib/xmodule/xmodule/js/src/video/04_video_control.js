(function (requirejs, require, define) {

// VideoControl module.
define(
'video/04_video_control.js',
[],
function () {

    // VideoControl() function - what this module "exports".
    return function (state) {
        var dfd = $.Deferred();

        state.videoControl = {};

        _makeFunctionsPublic(state);
        _renderElements(state);
        _bindHandlers(state);

        dfd.resolve();
        return dfd.promise();
    };

    // ***************************************************************
    // Private functions start here.
    // ***************************************************************

    // function _makeFunctionsPublic(state)
    //
    //     Functions which will be accessible via 'state' object. When called, these functions will
    //     get the 'state' object as a context.
    function _makeFunctionsPublic(state) {
        var methodsDict = {
            exitFullScreenHandler: exitFullScreenHandler,
            hideControls: hideControls,
            hidePlayPlaceholder: hidePlayPlaceholder,
            pause: pause,
            play: play,
            show: show,
            showControls: showControls,
            showPlayPlaceholder: showPlayPlaceholder,
            toggleFullScreen: toggleFullScreen,
            toggleFullScreenHandler: toggleFullScreenHandler,
            togglePlayback: togglePlayback,
            updateControlsHeight: updateControlsHeight,
            updateVcrVidTime: updateVcrVidTime
        };

        state.bindTo(methodsDict, state.videoControl, state);
    }

    // function _renderElements(state)
    //
    //     Create any necessary DOM elements, attach them, and set their initial configuration. Also
    //     make the created DOM elements available via the 'state' object. Much easier to work this
    //     way - you don't have to do repeated jQuery element selects.
    function _renderElements(state) {
        state.videoControl.el = state.el.find('.video-controls');
        // state.videoControl.el.append(el);

        state.videoControl.sliderEl            = state.videoControl.el.find('.slider');
        state.videoControl.playPauseEl         = state.videoControl.el.find('.video_control');
        state.videoControl.playPlaceholder     = state.el.find('.btn-play');
        state.videoControl.secondaryControlsEl = state.videoControl.el.find('.secondary-controls');
        state.videoControl.fullScreenEl        = state.videoControl.el.find('.add-fullscreen');
        state.videoControl.vidTimeEl           = state.videoControl.el.find('.vidtime');

        state.videoControl.fullScreenState = false;
        state.videoControl.pause();

        if (state.isTouch && state.videoType === 'html5') {
            state.videoControl.showPlayPlaceholder();
        }

        if ((state.videoType === 'html5') && (state.config.autohideHtml5)) {
            state.videoControl.fadeOutTimeout = state.config.fadeOutTimeout;

            state.videoControl.el.addClass('html5');
            state.controlHideTimeout = setTimeout(state.videoControl.hideControls, state.videoControl.fadeOutTimeout);
        }

        // ARIA
        // Let screen readers know that this anchor, representing the slider
        // handle, behaves as a slider named 'video slider'.
        state.videoControl.sliderEl.find('.ui-slider-handle').attr({
            'role': 'slider',
            'title': gettext('Video slider')
        });

        state.videoControl.updateControlsHeight();
    }

    // function _bindHandlers(state)
    //
    //     Bind any necessary function callbacks to DOM events (click, mousemove, etc.).
    function _bindHandlers(state) {
        state.videoControl.playPauseEl.on('click', state.videoControl.togglePlayback);
        state.videoControl.fullScreenEl.on('click', state.videoControl.toggleFullScreenHandler);
        state.el.on('fullscreen', function (event, isFullScreen) {
            var height = state.videoControl.updateControlsHeight();

            if (isFullScreen) {
                state.resizer
                    .delta
                    .substract(height, 'height')
                    .setMode('both');

            } else {
                state.resizer
                    .delta
                    .reset()
                    .setMode('width');
            }
        });

        $(document).on('keyup', state.videoControl.exitFullScreenHandler);

        if ((state.videoType === 'html5') && (state.config.autohideHtml5)) {
            state.el.on('mousemove', state.videoControl.showControls);
            state.el.on('keydown', state.videoControl.showControls);
        }
        // The state.previousFocus is used in video_speed_control to track
        // the element that had the focus before it.
        state.videoControl.playPauseEl.on('blur', function () {
            state.previousFocus = 'playPause';
        });

        if (/iPad|Android/i.test(state.isTouch[0])) {
            state.videoControl.playPlaceholder
                .on('click', function () {
                    state.trigger('videoPlayer.play', null);
                });
        }
    }
    function _getControlsHeight(control) {
        return control.el.height() + 0.5 * control.sliderEl.height();
    }

    // ***************************************************************
    // Public functions start here.
    // These are available via the 'state' object. Their context ('this' keyword) is the 'state' object.
    // The magic private function that makes them available and sets up their context is makeFunctionsPublic().
    // ***************************************************************

    function updateControlsHeight () {
        this.videoControl.height = _getControlsHeight(this.videoControl);

        return this.videoControl.height;
    }

    function show() {
        this.videoControl.el.removeClass('is-hidden');
        this.el.trigger('controls:show', arguments);
    }

    function showControls(event) {
        if (!this.controlShowLock) {
            if (!this.captionsHidden) {
                return;
            }

            this.controlShowLock = true;

            if (this.controlState === 'invisible') {
                this.videoControl.el.show();
                this.controlState = 'visible';
            } else if (this.controlState === 'hiding') {
                this.videoControl.el.stop(true, false).css('opacity', 1).show();
                this.controlState = 'visible';
            } else if (this.controlState === 'visible') {
                clearTimeout(this.controlHideTimeout);
            }

            this.controlHideTimeout = setTimeout(this.videoControl.hideControls, this.videoControl.fadeOutTimeout);

            this.controlShowLock = false;
        }
    }

    function hideControls() {
        var _this;

        this.controlHideTimeout = null;

        if (!this.captionsHidden) {
            return;
        }

        this.controlState = 'hiding';

        _this = this;

        this.videoControl.el.fadeOut(this.videoControl.fadeOutTimeout, function () {
            _this.controlState = 'invisible';

            // If the focus was on the video control or the volume control,
            // then we must make sure to close these dialogs. Otherwise, after
            // next autofocus, these dialogs will be open, but the focus will
            // not be on them.
            _this.videoVolumeControl.el.removeClass('open');
            _this.videoSpeedControl.el.removeClass('open');

            _this.focusGrabber.enableFocusGrabber();
        });
    }

    function showPlayPlaceholder(event) {
        this.videoControl.playPlaceholder
            .removeClass('is-hidden')
            .attr({
                'aria-hidden': 'false',
                'tabindex': 0
            });
    }

    function hidePlayPlaceholder(event) {
        this.videoControl.playPlaceholder
            .addClass('is-hidden')
            .attr({
                'aria-hidden': 'true',
                'tabindex': -1
            });
    }

    function play() {
        this.videoControl.isPlaying = true;
        this.videoControl.playPauseEl
            .removeClass('play')
            .addClass('pause')
            .attr('title', gettext('Pause'));

        if (/iPad|Android/i.test(this.isTouch[0]) && this.videoType === 'html5') {
            this.videoControl.hidePlayPlaceholder();
        }
    }

    function pause() {
        this.videoControl.isPlaying = false;
        this.videoControl.playPauseEl
            .removeClass('pause')
            .addClass('play')
            .attr('title', gettext('Play'));

        if (/iPad|Android/i.test(this.isTouch[0]) && this.videoType === 'html5') {
            this.videoControl.showPlayPlaceholder();
        }
    }

    function togglePlayback(event) {
        event.preventDefault();
        this.videoCommands.execute('togglePlayback');
    }

    /**
     * Event handler to toggle fullscreen mode.
     * @param {jquery Event} event
     */
    function toggleFullScreenHandler(event) {
        event.preventDefault();
        this.videoCommands.execute('toggleFullScreen');
    }

    /** Toggle fullscreen mode. */
    function toggleFullScreen() {
        var fullScreenClassNameEl = this.el.add(document.documentElement),
            win = $(window), text;

        if (this.videoControl.fullScreenState) {
            this.videoControl.fullScreenState = this.isFullScreen = false;
            fullScreenClassNameEl.removeClass('video-fullscreen');
            text = gettext('Fill browser');
            win.scrollTop(this.scrollPos);
        } else {
            this.scrollPos = win.scrollTop();
            win.scrollTop(0);
            this.videoControl.fullScreenState = this.isFullScreen = true;
            fullScreenClassNameEl.addClass('video-fullscreen');
            text = gettext('Exit full browser');
        }

        this.videoControl.fullScreenEl
            .attr('title', text)
            .text(text);

        this.el.trigger('fullscreen', [this.isFullScreen]);
    }

    /**
     * Event handler to exit from fullscreen mode.
     * @param {jquery Event} event
     */
    function exitFullScreenHandler(event) {
        if ((this.isFullScreen) && (event.keyCode === 27)) {
            event.preventDefault();
            this.videoCommands.execute('toggleFullScreen');
        }
    }

    function updateVcrVidTime(params) {
        var endTime = (this.config.endTime !== null) ? this.config.endTime : params.duration;
        // in case endTime is accidentally specified as being greater than the video
        endTime = Math.min(endTime, params.duration);
        this.videoControl.vidTimeEl.html(Time.format(params.time) + ' / ' + Time.format(endTime));
    }

});

}(RequireJS.requirejs, RequireJS.require, RequireJS.define));
