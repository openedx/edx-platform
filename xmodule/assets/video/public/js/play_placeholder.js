import $ from 'jquery'; // jQuery import
import _ from 'underscore';

'use strict';

/**
 * Video Play placeholder control function.
 *
 * @constructor
 * @param {Object} state - The object containing the state of the video
 * @param {Object} i18n - The object containing strings with translations
 * @return {jQuery.Promise} - A resolved jQuery promise
 */
function VideoPlayPlaceholder(state, i18n) {
    if (!(this instanceof VideoPlayPlaceholder)) {
        return new VideoPlayPlaceholder(state, i18n);
    }

    _.bindAll(this, 'onClick', 'hide', 'show', 'destroy');
    this.state = state;
    this.state.videoPlayPlaceholder = this;
    this.i18n = i18n;
    this.initialize();

    return $.Deferred().resolve().promise();
}

VideoPlayPlaceholder.prototype = {
    destroy: function () {
        this.el.off('click', this.onClick);
        this.state.el.off({
            destroy: this.destroy,
            play: this.hide,
            'ended pause': this.show,
        });
        this.hide();
        delete this.state.videoPlayPlaceholder;
    },

    /**
     * Indicates whether the placeholder should be shown.
     * We display it for HTML5 videos on iPad and Android devices.
     * @return {Boolean}
     */
    shouldBeShown: function () {
        return /iPad|Android/i.test(this.state.isTouch[0]) && !this.state.isYoutubeType();
    },

    /** Initializes the module. */
    initialize: function () {
        if (!this.shouldBeShown()) {
            return false;
        }

        this.el = this.state.el.find('.btn-play');
        this.bindHandlers();
        this.show();
    },

    /** Bind any necessary function callbacks to DOM events. */
    bindHandlers: function () {
        this.el.on('click', this.onClick);
        this.state.el.on({
            destroy: this.destroy,
            play: this.hide,
            'ended pause': this.show,
        });
    },

    onClick: function () {
        this.state.videoCommands.execute('play');
    },

    hide: function () {
        this.el
            .addClass('is-hidden')
            .attr({'aria-hidden': 'true', tabindex: -1});
    },

    show: function () {
        this.el
            .removeClass('is-hidden')
            .attr({'aria-hidden': 'false', tabindex: 0});
    }
};

export {VideoPlayPlaceholder};