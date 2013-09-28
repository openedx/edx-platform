(function (requirejs, require, define) {

// VideoQualityControl module.
define(
'video/05_video_quality_control.js',
[],
function () {

    // VideoQualityControl() function - what this module "exports".
    return function (state) {
        // Changing quality for now only works for YouTube videos.
        if (state.videoType !== 'youtube') {
            return;
        }

        state.videoQualityControl = {};

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
        state.videoQualityControl.onQualityChange = _.bind(onQualityChange, state);
        state.videoQualityControl.toggleQuality   = _.bind(toggleQuality, state);
    }

    // function _renderElements(state)
    //
    //     Create any necessary DOM elements, attach them, and set their initial configuration. Also
    //     make the created DOM elements available via the 'state' object. Much easier to work this
    //     way - you don't have to do repeated jQuery element selects.
    function _renderElements(state) {
        state.videoQualityControl.el = state.el.find('a.quality_control');

        state.videoQualityControl.el.show();
        state.videoQualityControl.quality = null;

        // ARIA
        // Let screen readers know that:

        // this anchor behaves like a button
        state.videoQualityControl.el.attr('role', gettext('button'));

        // what its name is: (title attribute is set in video.html template):
        // HD
        
        // what its state is:
        state.videoQualityControl.el.attr('aria-disabled', 'false');
    }

    // function _bindHandlers(state)
    //
    //     Bind any necessary function callbacks to DOM events (click, mousemove, etc.).
    function _bindHandlers(state) {
        state.videoQualityControl.el.on('click', state.videoQualityControl.toggleQuality);
    }

    // ***************************************************************
    // Public functions start here.
    // These are available via the 'state' object. Their context ('this' keyword) is the 'state' object.
    // The magic private function that makes them available and sets up their context is makeFunctionsPublic().
    // ***************************************************************

    function onQualityChange(value) {
        this.videoQualityControl.quality = value;

        if (_.indexOf(this.config.availableQualities, value) !== -1) {
            this.videoQualityControl.el.addClass('active');
        } else {
            this.videoQualityControl.el.removeClass('active');
        }
    }

    // This function change quality of video.
    // Right now we haven't ability to choose quality of HD video,
    // 'hd720' will be played by default as HD video(this thing is hardcoded).
    // If suggested quality level is not available for the video,
    // then the quality will be set to the next lowest level that is available.
    // (large -> medium)
    function toggleQuality(event) {
        var newQuality,
            value = this.videoQualityControl.quality;

        event.preventDefault();

        if (_.indexOf(this.config.availableQualities, value) !== -1) {
            newQuality = 'large';
        } else {
            newQuality = 'hd720';
        }

        this.trigger('videoPlayer.handlePlaybackQualityChange', newQuality);
    }

});

}(RequireJS.requirejs, RequireJS.require, RequireJS.define));
