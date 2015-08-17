(function (requirejs, require, define) {

// VideoQualityControl module.
define(
'video/05_video_quality_control.js',
[],
function () {
    var template = [
        '<a href="#" class="quality-control is-hidden" title="',
            gettext('HD off'), '" role="button" aria-disabled="false">',
            gettext('HD off'),
        '</a>'
    ].join('');

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
            destroy: destroy,
            fetchAvailableQualities: fetchAvailableQualities,
            onQualityChange: onQualityChange,
            showQualityControl: showQualityControl,
            toggleQuality: toggleQuality
        };

        state.bindTo(methodsDict, state.videoQualityControl, state);
    }

    function destroy() {
        this.videoQualityControl.el.off({
            'click': this.videoQualityControl.toggleQuality,
            'destroy': this.videoQualityControl.destroy
        });
        this.el.off('.quality');
        this.videoQualityControl.el.remove();
        delete this.videoQualityControl;
    }

    // function _renderElements(state)
    //
    //     Create any necessary DOM elements, attach them, and set their initial configuration. Also
    //     make the created DOM elements available via the 'state' object. Much easier to work this
    //     way - you don't have to do repeated jQuery element selects.
    function _renderElements(state) {
        var element = state.videoQualityControl.el = $(template);
        state.videoQualityControl.quality = 'large';
        state.el.find('.secondary-controls').append(element);
    }

    // function _bindHandlers(state)
    //
    //     Bind any necessary function callbacks to DOM events (click, mousemove, etc.).
    function _bindHandlers(state) {
        state.videoQualityControl.el.on('click',
            state.videoQualityControl.toggleQuality
        );
        state.el.on('play.quality', _.once(
            state.videoQualityControl.fetchAvailableQualities
        ));

        state.el.on('destroy.quality', state.videoQualityControl.destroy);
    }

    // ***************************************************************
    // Public functions start here.
    // These are available via the 'state' object. Their context ('this' keyword) is the 'state' object.
    // The magic private function that makes them available and sets up their context is makeFunctionsPublic().
    // ***************************************************************

    /*
     * @desc Shows quality control. This function will only be called if HD
     *       qualities are available.
     *
     * @public
     */
    function showQualityControl() {
        this.videoQualityControl.el.removeClass('is-hidden');
    }

    // This function can only be called once as _.once has been used.
    /*
     * @desc Get the available qualities from YouTube API. Possible values are:
             ['highres', 'hd1080', 'hd720', 'large', 'medium', 'small'].
             HD are: ['highres', 'hd1080', 'hd720'].
     *
     * @public
     */
    function fetchAvailableQualities() {
        var qualities = this.videoPlayer.player.getAvailableQualityLevels();

        this.config.availableHDQualities = _.intersection(
            qualities, ['highres', 'hd1080', 'hd720']
        );

        // HD qualities are available, show video quality control.
        if (this.config.availableHDQualities.length > 0) {
            this.trigger('videoQualityControl.showQualityControl');
            this.trigger('videoQualityControl.onQualityChange', this.videoQualityControl.quality);
        }
        // On initialization, force the video quality to be 'large' instead of
        // 'default'. Otherwise, the player will sometimes switch to HD
        // automatically, for example when the iframe resizes itself.
        this.trigger('videoPlayer.handlePlaybackQualityChange',
            this.videoQualityControl.quality
        );
    }

    function onQualityChange(value) {
        var controlStateStr;
        this.videoQualityControl.quality = value;
        if (_.contains(this.config.availableHDQualities, value)) {
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

    // This function toggles the quality of video only if HD qualities are
    // available.
    function toggleQuality(event) {
        var newQuality, value = this.videoQualityControl.quality,
            isHD = _.contains(this.config.availableHDQualities, value);

        event.preventDefault();

        newQuality = isHD ? 'large' : 'highres';

        this.trigger('videoPlayer.handlePlaybackQualityChange', newQuality);
    }

});

}(RequireJS.requirejs, RequireJS.require, RequireJS.define));
