(function (requirejs, require, define) {

// VideoQualityControl module.
define(
'video/05_video_quality_control.js',
[],
function () {

    // VideoQualityControl() function - what this module "exports".
    return function (state) {
        var dfd = $.Deferred();

        // Changing quality for now only works for YouTube videos.
        if (state.videoType !== 'youtube') {
            return;
        }

        state.videoQualityControl = {};

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
            onQualityChange: onQualityChange,
            toggleQuality: toggleQuality
        };

        state.bindTo(methodsDict, state.videoQualityControl, state);
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
        var controlStateStr;
        this.videoQualityControl.quality = value;

        if (_.indexOf(this.config.availableQualities, value) !== -1) {
            controlStateStr = gettext('HD on');
            this.videoQualityControl.el
                                    .addClass('active')
                                    .attr('title', controlStateStr)
                                    .text(controlStateStr);
        } else {
            controlStateStr = gettext('HD off');
            this.videoQualityControl.el
                                    .removeClass('active')
                                    .attr('title', controlStateStr)
                                    .text(controlStateStr);

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
