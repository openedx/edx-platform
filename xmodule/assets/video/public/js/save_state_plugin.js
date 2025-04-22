import $ from 'jquery';
import _ from 'underscore';
import Time from 'time.js';

'use strict';

/**
 * Save state module.
 *
 * @constructor
 * @param {Object} state - The object containing the state of the video
 * @param {Object} i18n - The object containing strings with translations
 * @param {Object} options - Options (e.g., events to handle)
 * @return {jQuery.Promise} - A resolved jQuery promise
 */
function VideoSaveStatePlugin(state, i18n, options) {
    if (!(this instanceof VideoSaveStatePlugin)) {
        return new VideoSaveStatePlugin(state, i18n, options);
    }

    _.bindAll(
        this,
        'onSpeedChange',
        'onAutoAdvanceChange',
        'saveStateHandler',
        'bindUnloadHandler',
        'onUnload',
        'onYoutubeAvailability',
        'onLanguageChange',
        'destroy'
    );

    this.state = state;
    this.options = _.extend({events: []}, options);
    this.state.videoSaveStatePlugin = this;
    this.i18n = i18n;
    this.initialize();

    return $.Deferred().resolve().promise();
}

VideoSaveStatePlugin.moduleName = 'SaveStatePlugin';
VideoSaveStatePlugin.prototype = {
    /**
     * Initializes the save state plugin and binds required handlers
     */
    initialize: function () {
        this.events = {
            speedchange: this.onSpeedChange,
            autoadvancechange: this.onAutoAdvanceChange,
            play: this.bindUnloadHandler,
            'pause destroy': this.saveStateHandler,
            'language_menu:change': this.onLanguageChange,
            youtube_availability: this.onYoutubeAvailability,
        };
        this.bindHandlers();
    },

    /**
     * Binds the appropriate event handlers to the state element or user-provided events
     */
    bindHandlers: function () {
        if (this.options.events.length) {
            _.each(
                this.options.events,
                function (eventName) {
                    if (_.has(this.events, eventName)) {
                        const callback = this.events[eventName];
                        this.state.el.on(eventName, callback);
                    }
                },
                this
            );
        } else {
            this.state.el.on(this.events);
        }
        this.state.el.on('destroy', this.destroy);
    },

    /**
     * Binds the unload event handler once
     */
    bindUnloadHandler: _.once(function () {
        $(window).on('unload.video', this.onUnload);
    }),

    /**
     * Cleans up the plugin by removing event handlers and deleting the instance
     */
    destroy: function () {
        this.state.el.off(this.events).off('destroy', this.destroy);
        $(window).off('unload.video', this.onUnload);
        delete this.state.videoSaveStatePlugin;
    },

    /**
     * Handles speed change events
     *
     * @param {Event} event - The event object
     * @param {number} newSpeed - The new playback speed
     */
    onSpeedChange: function (event, newSpeed) {
        this.saveState(true, {speed: newSpeed});
        this.state.storage.setItem('speed', newSpeed, true);
        this.state.storage.setItem('general_speed', newSpeed);
    },

    /**
     * Handles auto-advance toggle events
     *
     * @param {Event} event - The event object
     * @param {boolean} enabled - Whether auto-advance is enabled
     */
    onAutoAdvanceChange: function (event, enabled) {
        this.saveState(true, {auto_advance: enabled});
        this.state.storage.setItem('auto_advance', enabled);
    },

    /**
     * Saves the state when triggered directly by an event
     */
    saveStateHandler: function () {
        this.saveState(true);
    },

    /**
     * Saves the state during a `window.unload` event
     */
    onUnload: function () {
        this.saveState();
    },

    /**
     * Handles language change events
     *
     * @param {Event} event - The event object
     * @param {string} langCode - The new language code
     */
    onLanguageChange: function (event, langCode) {
        this.state.storage.setItem('language', langCode);
    },

    /**
     * Handles YouTube availability changes
     *
     * @param {Event} event - The event object
     * @param {boolean} youtubeIsAvailable - Whether YouTube is available
     */
    onYoutubeAvailability: function (event, youtubeIsAvailable) {
        if (youtubeIsAvailable !== this.state.config.recordedYoutubeIsAvailable) {
            this.saveState(true, {youtube_is_available: youtubeIsAvailable});
        }
    },

    /**
     * Saves the current state of the video
     *
     * @param {boolean} async - Whether to save asynchronously
     * @param {Object} [additionalData] - Additional data to save
     */
    saveState: function (async, data) {
        if (this.state.config.saveStateEnabled) {
            if (!($.isPlainObject(data))) {
                data = {
                    saved_video_position: this.state.videoPlayer.currentTime
                };
            }

            if (data.speed) {
                this.state.storage.setItem('speed', data.speed, true);
            }

            if (_.has(data, 'saved_video_position')) {
                this.state.storage.setItem('savedVideoPosition', data.saved_video_position, true);
                data.saved_video_position = Time.formatFull(data.saved_video_position);
            }

            $.ajax({
                url: this.state.config.saveStateUrl,
                type: 'POST',
                async: !!async,
                dataType: 'json',
                data: data
            });
        }
    },
};

export {VideoSaveStatePlugin};
