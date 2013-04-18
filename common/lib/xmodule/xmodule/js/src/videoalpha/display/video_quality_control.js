(function (requirejs, require, define) {

// VideoQualityControl module.
define(
'videoalpha/display/video_quality_control.js',
[],
function () {

    // VideoQualityControl() function - what this module "exports".
    return function (state) {
        // Changing quality for now only works for YouTube videos.
        if (state.videoType !== 'youtube') {
            return;
        }

        state.videoQualityControl = {};

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
        state.videoQualityControl.onQualityChange = onQualityChange.bind(state);
        state.videoQualityControl.toggleQuality   = toggleQuality.bind(state);
    }

    // function renderElements(state)
    //
    //     Create any necessary DOM elements, attach them, and set their initial configuration. Also
    //     make the created DOM elements available via the 'state' object. Much easier to work this
    //     way - you don't have to do repeated jQuery element selects.
    function renderElements(state) {
        state.videoQualityControl.el = state.el.find('a.quality_control');

        state.videoQualityControl.quality = null;

        if (!onTouchBasedDevice()) {
            // REFACTOR: Move qtip config to state.config
            state.videoQualityControl.el.qtip({
                'position': {
                    'my': 'top right',
                    'at': 'top center'
                }
            });
        }
    }

    // function bindHandlers(state)
    //
    //     Bind any necessary function callbacks to DOM events (click, mousemove, etc.).
    function bindHandlers(state) {
        state.videoQualityControl.el.on('click', state.videoQualityControl.toggleQuality);
    }

    // ***************************************************************
    // Public functions start here.
    // These are available via the 'state' object. Their context ('this' keyword) is the 'state' object.
    // The magic private function that makes them available and sets up their context is makeFunctionsPublic().
    // ***************************************************************

    function onQualityChange(value) {
        this.videoQualityControl.quality = value;

        // refactor: Move constants to state.config.
        if ((value === 'hd720') || (value === 'hd1080') || (value === 'highres')) {
            this.videoQualityControl.el.addClass('active');
        } else {
            this.videoQualityControl.el.removeClass('active');
        }
    }

    function toggleQuality(event) {
        var newQuality, _ref;

        event.preventDefault();

        _ref = this.videoQualityControl.quality;

        // refactor: Move constants to state.config.
        if ((_ref === 'hd720') || (_ref === 'hd1080') || (_ref === 'highres')) {
            newQuality = 'large';
        } else {
            newQuality = 'hd720';
        }

        this.trigger(['videoPlayer', 'handlePlaybackQualityChange'], newQuality);
    }

});

}(RequireJS.requirejs, RequireJS.require, RequireJS.define));
