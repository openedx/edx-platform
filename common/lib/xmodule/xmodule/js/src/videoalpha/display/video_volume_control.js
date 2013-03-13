(function (requirejs, require, define) {

// VideoVolumeControl module.
define(
'videoalpha/display/video_volume_control.js',
['videoalpha/display/bind.js'],
function (bind) {

    // VideoVolumeControl() function - what this module "exports".
    return function (state) {
        state.videoVolumeControl = {};

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
        state.videoVolumeControl.onChange = bind(onChange, state);
        state.videoVolumeControl.toggleMute = bind(toggleMute, state);
    }

    // function renderElements(state)
    //
    //     Create any necessary DOM elements, attach them, and set their initial configuration. Also
    //     make the created DOM elements available via the 'state' object. Much easier to work this
    //     way - you don't have to do repeated jQuery element selects.
    function renderElements(state) {
        state.videoVolumeControl.el = $(
            '<div class="volume">' +
                '<a href="#"></a>' +
                '<div class="volume-slider-container">' +
                    '<div class="volume-slider"></div>' +
                '</div>' +
            '</div>'
        );

        state.videoVolumeControl.buttonEl = state.videoVolumeControl.el.find('a');
        state.videoVolumeControl.volumeSliderEl = state.videoVolumeControl.el.find('.volume-slider');

        state.videoControl.secondaryControlsEl.prepend(state.videoVolumeControl.el);

        // Figure out what the current volume is. Set it up so that muting/unmuting works correctly.
        // If no information about volume level could be retrieved, then we will use the default
        // 100 level (full volume).
        state.videoVolumeControl.currentVolume = parseInt($.cookie('video_player_volume_level'), 10);
        state.videoVolumeControl.previousVolume = 100;
        if (
            (isFinite(state.videoVolumeControl.currentVolume) === false) ||
            (state.videoVolumeControl.currentVolume < 0) ||
            (state.videoVolumeControl.currentVolume > 100)
        ) {
            state.videoVolumeControl.currentVolume = 100;
        }

        state.videoVolumeControl.slider = state.videoVolumeControl.volumeSliderEl.slider({
            'orientation': 'vertical',
            'range': 'min',
            'min': 0,
            'max': 100,
            'value': state.videoVolumeControl.currentVolume,
            'change': state.videoVolumeControl.onChange,
            'slide': state.videoVolumeControl.onChange
        });

        state.videoVolumeControl.el.toggleClass('muted', state.videoVolumeControl.currentVolume === 0);
    }

    // function bindHandlers(state)
    //
    //     Bind any necessary function callbacks to DOM events (click, mousemove, etc.).
    function bindHandlers(state) {
        state.videoVolumeControl.buttonEl.on('click', state.videoVolumeControl.toggleMute);

        state.videoVolumeControl.el.on('mouseenter', function() {
            $(this).addClass('open');
        });

        state.videoVolumeControl.el.on('mouseleave', function() {
            $(this).removeClass('open');
        });
    }

    // ***************************************************************
    // Public functions start here.
    // These are available via the 'state' object. Their context ('this' keyword) is the 'state' object.
    // The magic private function that makes them available and sets up their context is makeFunctionsPublic().
    // ***************************************************************

    function onChange(event, ui) {
        this.videoVolumeControl.currentVolume = ui.value;
        this.videoVolumeControl.el.toggleClass('muted', this.videoVolumeControl.currentVolume === 0);

        $.cookie('video_player_volume_level', ui.value, {
            'expires': 3650,
            'path': '/'
        });

        this.trigger(['videoPlayer', 'onVolumeChange'], ui.value, 'method');
    }

    function toggleMute(event) {
        event.preventDefault();

        if (this.videoVolumeControl.currentVolume > 0) {
            this.videoVolumeControl.previousVolume = this.videoVolumeControl.currentVolume;
            this.videoVolumeControl.slider.slider('option', 'value', 0);
        } else {
            this.videoVolumeControl.slider.slider('option', 'value', this.videoVolumeControl.previousVolume);
        }
    }

});

}(RequireJS.requirejs, RequireJS.require, RequireJS.define));
