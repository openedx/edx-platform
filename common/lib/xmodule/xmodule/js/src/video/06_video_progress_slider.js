(function (requirejs, require, define) {

/*
"This is as true in everyday life as it is in battle: we are given one life
and the decision is ours whether to wait for circumstances to make up our
mind, or whether to act, and in acting, to live."
— Omar N. Bradley
 */

// VideoProgressSlider module.
define(
'video/06_video_progress_slider.js',
[],
function () {

    // VideoProgressSlider() function - what this module "exports".
    return function (state) {
        state.videoProgressSlider = {};

        _makeFunctionsPublic(state);
        _renderElements(state);
        // No callbacks to DOM events (click, mousemove, etc.).
    };

    // ***************************************************************
    // Private functions start here.
    // ***************************************************************

    // function _makeFunctionsPublic(state)
    //
    //     Functions which will be accessible via 'state' object. When called, these functions will
    //     get the 'state' object as a context.
    function _makeFunctionsPublic(state) {
        state.videoProgressSlider.onSlide        = _.bind(onSlide, state);
        state.videoProgressSlider.onStop         = _.bind(onStop, state);
        state.videoProgressSlider.updatePlayTime = _.bind(updatePlayTime, state);
        //Added for tests -- JM
        state.videoProgressSlider.buildSlider = _.bind(buildSlider, state);
    }

    // function _renderElements(state)
    //
    //     Create any necessary DOM elements, attach them, and set their initial configuration. Also
    //     make the created DOM elements available via the 'state' object. Much easier to work this
    //     way - you don't have to do repeated jQuery element selects.
    function _renderElements(state) {
        if (!onTouchBasedDevice()) {
            state.videoProgressSlider.el = state.videoControl.sliderEl;

            buildSlider(state);
            _buildHandle(state);
        }
    }

    function _buildHandle(state) {
        state.videoProgressSlider.handle = state.videoProgressSlider.el.find('.ui-slider-handle');
    }

    // ***************************************************************
    // Public functions start here.
    // These are available via the 'state' object. Their context ('this' keyword) is the 'state' object.
    // The magic private function that makes them available and sets up their context is makeFunctionsPublic().
    // ***************************************************************

    function buildSlider(state) {
        state.videoProgressSlider.slider = state.videoProgressSlider.el.slider({
            range: 'min',
            slide: state.videoProgressSlider.onSlide,
            stop: state.videoProgressSlider.onStop
        });
    }

    function onSlide(event, ui) {
        this.videoProgressSlider.frozen = true;

        this.trigger('videoPlayer.onSlideSeek', {'type': 'onSlideSeek', 'time': ui.value});
    }

    function onStop(event, ui) {
        var _this = this;

        this.videoProgressSlider.frozen = true;

        this.trigger('videoPlayer.onSlideSeek', {'type': 'onSlideSeek', 'time': ui.value});

        setTimeout(function() {
            _this.videoProgressSlider.frozen = false;
        }, 200);
    }

    //Changed for tests -- JM: Check if it is the cause of Chrome Bug Valera noticed
    function updatePlayTime(params) {
        if ((this.videoProgressSlider.slider) && (!this.videoProgressSlider.frozen)) {
            /*this.videoProgressSlider.slider
                .slider('option', 'max', params.duration)
                .slider('value', params.time);*/
            this.videoProgressSlider.slider.slider('option', 'max', params.duration);
            this.videoProgressSlider.slider.slider('option', 'value', params.time);
        }
    }

});

}(RequireJS.requirejs, RequireJS.require, RequireJS.define));
