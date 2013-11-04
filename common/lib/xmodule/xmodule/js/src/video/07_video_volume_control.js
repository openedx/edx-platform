(function (requirejs, require, define) {

// VideoVolumeControl module.
define(
'video/07_video_volume_control.js',
[],
function () {

    // VideoVolumeControl() function - what this module "exports".
    return function (state) {
        state.videoVolumeControl = {};

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
        var methodsDict = {
            onChange: onChange,
            toggleMute: toggleMute
        };

        state.bindTo(methodsDict, state.videoVolumeControl, state);
    }

    // function _renderElements(state)
    //
    //     Create any necessary DOM elements, attach them, and set their initial configuration. Also
    //     make the created DOM elements available via the 'state' object. Much easier to work this
    //     way - you don't have to do repeated jQuery element selects.
    function _renderElements(state) {
        state.videoVolumeControl.el = state.el.find('div.volume');

        state.videoVolumeControl.buttonEl = state.videoVolumeControl.el.find('a');
        state.videoVolumeControl.volumeSliderEl = state.videoVolumeControl.el.find('.volume-slider');

        state.videoControl.secondaryControlsEl.prepend(state.videoVolumeControl.el);

        // Figure out what the current volume is. If no information about volume level could be retrieved,
        // then we will use the default 100 level (full volume).
        state.videoVolumeControl.currentVolume = parseInt($.cookie('video_player_volume_level'), 10);
        if (!isFinite(state.videoVolumeControl.currentVolume)) {
            state.videoVolumeControl.currentVolume = 100;
        }

        // Set it up so that muting/unmuting works correctly.
        state.videoVolumeControl.previousVolume = 100;

        state.videoVolumeControl.slider = state.videoVolumeControl.volumeSliderEl.slider({
            orientation: 'vertical',
            range: 'min',
            min: 0,
            max: 100,
            value: state.videoVolumeControl.currentVolume,
            change: state.videoVolumeControl.onChange,
            slide: state.videoVolumeControl.onChange
        });

        state.videoVolumeControl.el.toggleClass('muted', state.videoVolumeControl.currentVolume === 0);

        // ARIA
        // Let screen readers know that:

        // This anchor behaves as a button named 'Volume'.
        var currentVolume = state.videoVolumeControl.currentVolume,
            buttonStr = (currentVolume === 0) ? 'Volume muted' : 'Volume';
        // We add the aria-label attribute because the title attribute cannot be
        // read.
        state.videoVolumeControl.buttonEl.attr('aria-label', gettext(buttonStr));

        // Let screen readers know that this anchor, representing the slider
        // handle, behaves as a slider named 'volume'.
        var volumeSlider = state.videoVolumeControl.slider;
        state.videoVolumeControl.volumeSliderHandleEl = state.videoVolumeControl
                                                             .volumeSliderEl
                                                             .find('.ui-slider-handle');
        state.videoVolumeControl.volumeSliderHandleEl.attr({
            'role': 'slider',
            'title': 'volume',
            'aria-disabled': false,
            'aria-valuemin': volumeSlider.slider('option', 'min'),
            'aria-valuemax': volumeSlider.slider('option', 'max'),
            'aria-valuenow': volumeSlider.slider('option', 'value'),
            'aria-valuetext': getVolumeDescription(volumeSlider.slider('option', 'value'))
        });
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
        state.videoVolumeControl.buttonEl
            .on('click', state.videoVolumeControl.toggleMute);

        state.videoVolumeControl.el.on('mouseenter', function() {
            state.videoVolumeControl.el.addClass('open');
        });

        state.videoVolumeControl.el.on('mouseleave', function() {
            state.videoVolumeControl.el.removeClass('open');
        });

        // Attach a focus event to the volume button.
        state.videoVolumeControl.buttonEl.on('blur', function() {
            // If the focus is being trasnfered from the volume slider, then we
            // don't do anything except for unsetting the special flag.
            if (state.volumeBlur === true) {
                state.volumeBlur = false;
            }

            //If the focus is comming from elsewhere, then we must show the
            // volume slider and set focus to it.
            else {
                state.videoVolumeControl.el.addClass('open');
                state.videoVolumeControl.volumeSliderEl.find('a').focus();
            }
        });

        // Attach a blur event handler (loss of focus) to the volume slider
        // element. More specifically, we are attaching to the handle on
        // the slider with which you can change the volume.
        state.videoVolumeControl.volumeSliderEl.find('a')
            .on('blur', function () {
                // Hide the volume slider. This is done so that we can
                // continue to the next (or previous) element by tabbing.
                // Otherwise, after next tab we would come back to the volume
                // slider because it is the next element visible element that
                // we can tab to after the volume button.
                state.videoVolumeControl.el.removeClass('open');

                // Set focus to the volume button.
                state.videoVolumeControl.buttonEl.focus();

                // We store the fact that previous element that lost focus was
                // the volume clontrol.
                state.volumeBlur = true;
                // The following field is used in video_speed_control to track
                // the element that had the focus before it.
                state.previousFocus = 'volume';
            });
    }

    // ***************************************************************
    // Public functions start here.
    // These are available via the 'state' object. Their context ('this' keyword) is the 'state' object.
    // The magic private function that makes them available and sets up their context is makeFunctionsPublic().
    // ***************************************************************

    function onChange(event, ui) {
        var currentVolume = ui.value,
            ariaLabelText = (currentVolume === 0) ? 'Volume muted' : 'Volume';

        this.videoVolumeControl.currentVolume = currentVolume;
        this.videoVolumeControl.el.toggleClass('muted', currentVolume === 0);

        $.cookie('video_player_volume_level', ui.value, {
            expires: 3650,
            path: '/'
        });

        this.trigger('videoPlayer.onVolumeChange', ui.value);

        // ARIA
        this.videoVolumeControl.volumeSliderHandleEl.attr({
            'aria-valuenow': ui.value,
            'aria-valuetext': getVolumeDescription(ui.value)
        });

        this.videoVolumeControl.buttonEl.attr(
            'aria-label', gettext(ariaLabelText)
        );
    }

    function toggleMute(event) {
        event.preventDefault();

        if (this.videoVolumeControl.currentVolume > 0) {
            this.videoVolumeControl.previousVolume = this.videoVolumeControl.currentVolume;
            this.videoVolumeControl.slider.slider('option', 'value', 0);
            // ARIA
            this.videoVolumeControl.volumeSliderHandleEl.attr({
                'aria-valuenow': 0,
                'aria-valuetext': getVolumeDescription(0),
            });
        } else {
            this.videoVolumeControl.slider.slider('option', 'value', this.videoVolumeControl.previousVolume);
            // ARIA
            this.videoVolumeControl.volumeSliderHandleEl.attr({
                'aria-valuenow': this.videoVolumeControl.previousVolume,
                'aria-valuetext': getVolumeDescription(this.videoVolumeControl.previousVolume)
            });
        }
    }

    // ARIA
    // Returns a string describing the level of volume.
    function getVolumeDescription(vol) {
        if (vol === 0) {
            return 'muted';
        } else if (vol <= 20) {
            return 'very low';
        } else if (vol <= 40) {
            return 'low';
        } else if (vol <= 60) {
            return 'average';
        } else if (vol <= 80) {
            return 'loud';
        } else if (vol <= 99) {
            return 'very loud';
        }

        return 'maximum';
    }

});

}(RequireJS.requirejs, RequireJS.require, RequireJS.define));
