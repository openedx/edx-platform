(function (requirejs, require, define) {

/*
"This is as true in everyday life as it is in battle: we are given one life
and the decision is ours whether to wait for circumstances to make up our
mind, or whether to act, and in acting, to live."
— Omar N. Bradley
 */

// VideoProgressSlider module.
define(
'videoalpha/display/video_progress_slider.js',
['videoalpha/display/bind.js'],
function (bind) {

    // VideoProgressSlider() function - what this module "exports".
    return function (state) {
        state.videoProgressSlider = {};

        makeFunctionsPublic(state);
        renderElements(state);
        bindHandlers(state);
        registerCallbacks(state);
    };

    // ***************************************************************
    // Private functions start here.
    // ***************************************************************

    // function makeFunctionsPublic(state)
    //
    //     Functions which will be accessible via 'state' object. When called, these functions will
    //     get the 'state' object as a context.
    function makeFunctionsPublic(state) {
        state.videoProgressSlider.onSlide        = bind(onSlide, state);
        state.videoProgressSlider.onChange       = bind(onChange, state);
        state.videoProgressSlider.onStop         = bind(onStop, state);
        state.videoProgressSlider.updateTooltip  = bind(updateTooltip, state);
        state.videoProgressSlider.updatePlayTime = bind(updatePlayTime, state);
    }

    // function renderElements(state)
    //
    //     Create any necessary DOM elements, attach them, and set their initial configuration. Also
    //     make the created DOM elements available via the 'state' object. Much easier to work this
    //     way - you don't have to do repeated jQuery element selects.
    function renderElements(state) {
        if (!onTouchBasedDevice()) {
            state.videoProgressSlider.el = state.videoControl.sliderEl;

            buildSlider(state);
            buildHandle(state);
        }
    }

    // function bindHandlers(state)
    //
    //     Bind any necessary function callbacks to DOM events (click, mousemove, etc.).
    function bindHandlers(state) {

    }

    // function registerCallbacks(state)
    //
    //     Register function callbacks to be called by other modules.
    function registerCallbacks(state) {
        state.callbacks.videoPlayer.updatePlayTime.push(state.videoProgressSlider.updatePlayTime);
    }

    function buildSlider(state) {
        state.videoProgressSlider.slider = state.videoProgressSlider.el.slider({
            'range':  'min',
            'change': state.videoProgressSlider.onChange,
            'slide':  state.videoProgressSlider.onSlide,
            'stop':   state.videoProgressSlider.onStop
        });
    }

    function buildHandle(state) {
        state.videoProgressSlider.handle = state.videoProgressSlider.el.find('.ui-slider-handle');

        state.videoProgressSlider.handle.qtip({
            'content': '' + Time.format(state.videoProgressSlider.slider.slider('value')),
            'position': {
                'my': 'bottom center',
                'at': 'top center',
                'container': state.videoProgressSlider.handle
            },
            'hide': {
                'delay': 700
            },
            'style': {
                'classes': 'ui-tooltip-slider',
                'widget': true
            }
        });
    }

    // ***************************************************************
    // Public functions start here.
    // These are available via the 'state' object. Their context ('this' keyword) is the 'state' object.
    // The magic private function that makes them available and sets up their context is makeFunctionsPublic().
    // ***************************************************************

    function onSlide(event, ui) {
        this.videoProgressSlider.frozen = true;
        this.videoProgressSlider.updateTooltip(ui.value);

        $.each(this.callbacks.videoProgressSlider.onSlide, function (index, value) {
            // Each value is a registered callback (JavaScript function object).
            value(ui.value);
        });
    }

    function onChange(event, ui) {
        this.videoProgressSlider.updateTooltip(ui.value);
    }

    function onStop(event, ui) {
        var _this;

        _this = this;

        this.videoProgressSlider.frozen = true;

        $.each(this.callbacks.videoProgressSlider.onStop, function (index, value) {
            // Each value is a registered callback (JavaScript function object).
            value(ui.value);
        });

        setTimeout(function() {
            _this.videoProgressSlider.frozen = false;
        }, 200);
    }

    function updateTooltip(value) {
        this.videoProgressSlider.handle.qtip('option', 'content.text', '' + Time.format(value));
    }

    function updatePlayTime(currentTime, duration) {
        if ((this.videoProgressSlider.slider) && (!this.videoProgressSlider.frozen)) {
            this.videoProgressSlider.slider.slider('option', 'max', duration);
            this.videoProgressSlider.slider.slider('value', currentTime);
        }
    }

});

}(RequireJS.requirejs, RequireJS.require, RequireJS.define));
