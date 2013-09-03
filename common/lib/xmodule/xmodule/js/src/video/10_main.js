(function (requirejs, require, define) {

// Main module.
require(
[
    'video/01_initialize.js',
    'video/04_video_control.js',
    'video/05_video_quality_control.js',
    'video/06_video_progress_slider.js',
    'video/07_video_volume_control.js',
    'video/08_video_speed_control.js',
    'video/09_video_caption.js'
],
function (
    Initialize,
    VideoControl,
    VideoQualityControl,
    VideoProgressSlider,
    VideoVolumeControl,
    VideoSpeedControl,
    VideoCaption
) {
    var previousState,
        youtubeXhr = null;

    // Because this constructor can be called multiple times on a single page (when
    // the user switches verticals, the page doesn't reload, but the content changes), we must
    // will check each time if there is a previous copy of 'state' object. If there is, we
    // will make sure that copy exists cleanly. We have to do this because when verticals switch,
    // the code does not handle any Xmodule JS code that is running - it simply removes DOM
    // elements from the page. Any functions that were running during this, and that will run
    // afterwards (expecting the DOM elements to be present) must be stopped by hand.
    previousState = null;

    window.Video = function (element) {
        var state;

        // Stop bufferization of previous video on sequence change.
        // Problem: multiple video tags with the same src cannot
        // play together. The second tag waiting when first video will be fully loaded.
        // That's why we abort bufferization forcibly.
        $(element).closest('.sequence').bind('sequence:change', function(e){
            if (previousState !== null && typeof previousState.videoPlayer !== 'undefined') {
                previousState.stopBuffering();
                $(e.currentTarget).unbind('sequence:change');
            }
        });

        // Check for existance of previous state, uninitialize it if necessary, and create a new state.
        // Store new state for future invocation of this module consturctor function.
        if (previousState !== null && typeof previousState.videoPlayer !== 'undefined') {
            previousState.videoPlayer.onPause();
        }
        state = {};
        previousState = state;

        state.youtubeXhr = youtubeXhr;
        Initialize(state, element);
        if (!youtubeXhr) {
            youtubeXhr = state.youtubeXhr;
        }

        VideoControl(state);
        VideoQualityControl(state);
        VideoProgressSlider(state);
        VideoVolumeControl(state);
        VideoSpeedControl(state);
        VideoCaption(state);

        // Because the 'state' object is only available inside this closure, we will also make
        // it available to the caller by returning it. This is necessary so that we can test
        // Video with Jasmine.
        return state;
    };

    window.Video.clearYoutubeXhr = function () {
        youtubeXhr = null;
    };
});

}(RequireJS.requirejs, RequireJS.require, RequireJS.define));
