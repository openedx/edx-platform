(function (requirejs, require, define) {

// VideoControl module.
define(
'videoalpha/display/video_control.js',
[],
function () {

    // VideoControl() function - what this module "exports".
    return function (state) {
        state.videoControl = {};

        makeFunctionsPublic(state);
        renderElements(state);
        bindHandlers(state);
    };

    // ***************************************************************
    // Private functions start here.
    // ***************************************************************

    // function makeFunctionsPublic(state)
    //
    //     Functions which will be accessible via 'state' object. When called, these functions will
    //     get the 'state' object as a context.
    function makeFunctionsPublic(state) {
        state.videoControl.showControls     = showControls.bind(state);
        state.videoControl.hideControls     = hideControls.bind(state);
        state.videoControl.play             = play.bind(state);
        state.videoControl.pause            = pause.bind(state);
        state.videoControl.togglePlayback   = togglePlayback.bind(state);
        state.videoControl.toggleFullScreen = toggleFullScreen.bind(state);
        state.videoControl.exitFullScreen   = exitFullScreen.bind(state);
        state.videoControl.updateVcrVidTime = updateVcrVidTime.bind(state);
    }

    // function renderElements(state)
    //
    //     Create any necessary DOM elements, attach them, and set their initial configuration. Also
    //     make the created DOM elements available via the 'state' object. Much easier to work this
    //     way - you don't have to do repeated jQuery element selects.
    function renderElements(state) {
        var qTipConfig;

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

            qTipConfig = {
                'position': {
                    'my': 'top right',
                    'at': 'top center'
                }
            };

            state.videoControl.playPauseEl.qtip(qTipConfig);
            state.videoControl.fullScreenEl.qtip(qTipConfig);
        } else {
            state.videoControl.play();
        }

        if (state.videoType === 'html5') {
            // REFACTOR: constants move to initialize()
            
            state.videoControl.fadeOutTimeout = 1400;

            state.videoControl.el.addClass('html5');
            state.controlHideTimeout = setTimeout(state.videoControl.hideControls, state.videoControl.fadeOutTimeout);
        }
    }

    // function bindHandlers(state)
    //
    //     Bind any necessary function callbacks to DOM events (click, mousemove, etc.).
    function bindHandlers(state) {
        state.videoControl.playPauseEl.on('click', state.videoControl.togglePlayback);
        state.videoControl.fullScreenEl.on('click', state.videoControl.toggleFullScreen);
        $(document).on('keyup', state.videoControl.exitFullScreen);

        if (state.videoType === 'html5') {
            state.el.on('mousemove', state.videoControl.showControls)
        }
    }

    // ***************************************************************
    // Public functions start here.
    // These are available via the 'state' object. Their context ('this' keyword) is the 'state' object.
    // The magic private function that makes them available and sets up their context is makeFunctionsPublic().
    // ***************************************************************
    // REFACTOR document
    function showControls(event) {
        if (!this.controlShowLock) {
            if (!this.captionsHidden) {
                return;
            }

            this.controlShowLock = true;

            // Refactor: separate UI state in object. No code duplication.
            // REFACTOR:
            // 1.) Chain jQuery calls.
            // 2.) Drop out common code.
            if (this.controlState === 'invisible') {
                this.videoControl.el.show();
                this.controlState = 'visible';
                this.controlHideTimeout = setTimeout(this.videoControl.hideControls, this.videoControl.fadeOutTimeout);
            } else if (this.controlState === 'hiding') {
                this.videoControl.el.stop(true, false);
                this.videoControl.el.css('opacity', 1);
                this.videoControl.el.show();
                this.controlState = 'visible';
                this.controlHideTimeout = setTimeout(this.videoControl.hideControls, this.videoControl.fadeOutTimeout);
            } else if (this.controlState === 'visible') {
                clearTimeout(this.controlHideTimeout);
                this.controlHideTimeout = setTimeout(this.videoControl.hideControls, this.videoControl.fadeOutTimeout);
            }

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

        this.videoControl.el.fadeOut(1000, function () {
            _this.controlState = 'invisible';
        });
    }

    function play() {
        // REFACTOR: this.videoControl.playPauseState should be bool.
        this.videoControl.playPauseEl.removeClass('play').addClass('pause').attr('title', 'Pause');
        this.videoControl.playPauseState = 'playing';
    }

    function pause() {
        this.videoControl.playPauseEl.removeClass('pause').addClass('play').attr('title', 'Play');
        this.videoControl.playPauseState = 'paused';
    }

    function togglePlayback(event) {
        event.preventDefault();

        if (this.videoControl.playPauseState === 'playing') {
            this.trigger(['videoPlayer', 'pause'], null);
        } else { // if (this.videoControl.playPauseState === 'paused') {
            this.trigger(['videoPlayer', 'play'], null);
        }
    }

    function toggleFullScreen(event) {
        event.preventDefault();

        if (this.videoControl.fullScreenState) {
            this.videoControl.fullScreenState = false;
            this.el.removeClass('fullscreen');
            this.videoControl.fullScreenEl.attr('title', 'Fullscreen');
        } else {
            this.videoControl.fullScreenState = true;
            this.el.addClass('fullscreen');
            this.videoControl.fullScreenEl.attr('title', 'Exit fullscreen');
        }

        this.trigger(['videoCaption', 'resize'], null);
    }

    function exitFullScreen(event) {
        // REFACTOR: Add variable instead of class.
        if ((this.el.hasClass('fullscreen')) && (event.keyCode === 27)) {
            this.videoControl.toggleFullScreen(event);
        }
    }

    function updateVcrVidTime(params) {
        this.videoControl.vidTimeEl.html(Time.format(params.time) + ' / ' + Time.format(params.duration));
    }

});

}(RequireJS.requirejs, RequireJS.require, RequireJS.define));
