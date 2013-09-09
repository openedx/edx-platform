(function (requirejs, require, define) {

// VideoControl module.
define(
'video/04_video_control.js',
[],
function () {

    // VideoControl() function - what this module "exports".
    return function (state) {
        state.videoControl = {};

        _makeFunctionsPublic(state);
        _renderElements(state);
        _bindHandlers(state);
    };

    // ***************************************************************
    // Private functions start here.
    // ***************************************************************

    // function _makeFunctionsPublic(state)
    //
    //     Functions which will be accessible via 'state' object. When called, these functions will
    //     get the 'state' object as a context.
    function _makeFunctionsPublic(state) {
        state.videoControl.showControls     = _.bind(showControls,state);
        state.videoControl.hideControls     = _.bind(hideControls,state);
        state.videoControl.play             = _.bind(play,state);
        state.videoControl.pause            = _.bind(pause,state);
        state.videoControl.togglePlayback   = _.bind(togglePlayback,state);
        state.videoControl.toggleFullScreen = _.bind(toggleFullScreen,state);
        state.videoControl.exitFullScreen   = _.bind(exitFullScreen,state);
        state.videoControl.updateVcrVidTime = _.bind(updateVcrVidTime,state);
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
        state.videoControl.secondaryControlsEl = state.videoControl.el.find('.secondary-controls');
        state.videoControl.fullScreenEl        = state.videoControl.el.find('.add-fullscreen');
        state.videoControl.vidTimeEl           = state.videoControl.el.find('.vidtime');

        state.videoControl.fullScreenState = false;

        if (!onTouchBasedDevice()) {
            state.videoControl.pause();
        } else {
            state.videoControl.play();
        }

        if (state.videoType === 'html5') {
            state.videoControl.fadeOutTimeout = state.config.fadeOutTimeout;

            state.videoControl.el.addClass('html5');
            state.controlHideTimeout = setTimeout(state.videoControl.hideControls, state.videoControl.fadeOutTimeout);
        }
    }

    // function _bindHandlers(state)
    //
    //     Bind any necessary function callbacks to DOM events (click, mousemove, etc.).
    function _bindHandlers(state) {
        state.videoControl.playPauseEl.on('click', state.videoControl.togglePlayback);
        state.videoControl.fullScreenEl.on('click', state.videoControl.toggleFullScreen);
        $(document).on('keyup', state.videoControl.exitFullScreen);

        if (state.videoType === 'html5') {
            state.el.on('mousemove', state.videoControl.showControls);
            state.el.on('keydown', state.videoControl.showControls);
        }
        // The state.previousFocus is used in video_speed_control to track 
        // the element that had the focus before it.
        state.videoControl.playPauseEl.on('blur', function () {
            state.previousFocus = 'playPause';
        });
    }

    // ***************************************************************
    // Public functions start here.
    // These are available via the 'state' object. Their context ('this' keyword) is the 'state' object.
    // The magic private function that makes them available and sets up their context is makeFunctionsPublic().
    // ***************************************************************
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
        });
    }

    function play() {
        this.videoControl.playPauseEl.removeClass('play').addClass('pause').attr('title', gettext('Pause'));
        this.videoControl.isPlaying = true;
    }

    function pause() {
        this.videoControl.playPauseEl.removeClass('pause').addClass('play').attr('title', gettext('Play'));
        this.videoControl.isPlaying = false;
    }

    function togglePlayback(event) {
        event.preventDefault();

        if (this.videoControl.isPlaying) {
            this.trigger('videoPlayer.pause', null);
        } else {
            this.trigger('videoPlayer.play', null);
        }
    }

    function toggleFullScreen(event) {
        event.preventDefault();
        var fullScreenClassNameEl = this.el.add(document.documentElement);

        if (this.videoControl.fullScreenState) {
            this.videoControl.fullScreenState = false;
            fullScreenClassNameEl.removeClass('video-fullscreen');
            this.isFullScreen = false;
            this.videoControl.fullScreenEl.attr('title', gettext('Fullscreen'));
        } else {
            this.videoControl.fullScreenState = true;
            fullScreenClassNameEl.addClass('video-fullscreen');
            this.isFullScreen = true;
            this.videoControl.fullScreenEl.attr('title', gettext('Exit fullscreen'));
        }

        this.trigger('videoCaption.resize', null);
    }

    function exitFullScreen(event) {
        if ((this.isFullScreen) && (event.keyCode === 27)) {
            this.videoControl.toggleFullScreen(event);
        }
    }

    function updateVcrVidTime(params) {
        this.videoControl.vidTimeEl.html(Time.format(params.time) + ' / ' + Time.format(params.duration));
    }

});

}(RequireJS.requirejs, RequireJS.require, RequireJS.define));
