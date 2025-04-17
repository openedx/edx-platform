import $ from 'jquery';
import _ from 'underscore';

'use strict';

/**
 * Events module.
 *
 * @constructor
 * @param {Object} state - The object containing the state of the video
 * @param {Object} i18n - The object containing strings with translations
 * @param {Object} options - Additional options for the plugin
 * @return {jQuery.Promise} - A resolved jQuery promise
 */
function VideoEventsBumperPlugin(state, i18n, options) {
    if (!(this instanceof VideoEventsBumperPlugin)) {
        return new VideoEventsBumperPlugin(state, i18n, options);
    }

    _.bindAll(
        this,
        'onReady',
        'onPlay',
        'onEnded',
        'onShowLanguageMenu',
        'onHideLanguageMenu',
        'onSkip',
        'onShowCaptions',
        'onHideCaptions',
        'destroy'
    );

    this.state = state;
    this.options = _.extend({}, options);
    this.state.videoEventsBumperPlugin = this;
    this.i18n = i18n;

    this.initialize();

    return $.Deferred().resolve().promise();
}

VideoEventsBumperPlugin.moduleName = 'EventsBumperPlugin';

VideoEventsBumperPlugin.prototype = {
    /**
     * Initialize the plugin by binding the required event handlers
     */
    initialize: function () {
        this.events = {
            ready: this.onReady,
            play: this.onPlay,
            'ended stop': this.onEnded,
            skip: this.onSkip,
            'language_menu:show': this.onShowLanguageMenu,
            'language_menu:hide': this.onHideLanguageMenu,
            'captions:show': this.onShowCaptions,
            'captions:hide': this.onHideCaptions,
            destroy: this.destroy,
        };
        this.bindHandlers();
    },

    /**
     * Bind event handlers to the video state element
     */
    bindHandlers: function () {
        this.state.el.on(this.events);
    },

    /**
     * Cleanup by removing event handlers and destroying the plugin instance
     */
    destroy: function () {
        this.state.el.off(this.events);
        delete this.state.videoEventsBumperPlugin;
    },

    /**
     * Handle the `ready` event
     */
    onReady: function () {
        this.log('edx.video.bumper.loaded');
    },

    /**
     * Handle the `play` event
     */
    onPlay: function () {
        this.log('edx.video.bumper.played', { currentTime: this.getCurrentTime() });
    },

    /**
     * Handle the `ended` and `stop` events
     */
    onEnded: function () {
        this.log('edx.video.bumper.stopped', { currentTime: this.getCurrentTime() });
    },

    /**
     * Handle the `skip` event
     */
    onSkip: function (event, doNotShowAgain) {
        const info = { currentTime: this.getCurrentTime() };
        const eventName = `edx.video.bumper.${doNotShowAgain ? 'dismissed' : 'skipped'}`;
        this.log(eventName, info);
    },

    /**
     * Handle when the language menu is shown
     */
    onShowLanguageMenu: function () {
        this.log('edx.video.bumper.transcript.menu.shown');
    },

    /**
     * Handle when the language menu is hidden
     */
    onHideLanguageMenu: function () {
        this.log('edx.video.bumper.transcript.menu.hidden');
    },

    /**
     * Handle when captions are shown
     */
    onShowCaptions: function () {
        this.log('edx.video.bumper.transcript.shown', { currentTime: this.getCurrentTime() });
    },

    /**
     * Handle when captions are hidden
     */
    onHideCaptions: function () {
        this.log('edx.video.bumper.transcript.hidden', { currentTime: this.getCurrentTime() });
    },

    /**
     * Get the current time of the video
     *
     * @return {Number} - The current time of the video in seconds
     */
    getCurrentTime: function () {
        const player = this.state.videoPlayer;
        return player ? player.currentTime : 0;
    },

    /**
     * Get the duration of the video
     *
     * @return {Number} - The duration of the video in seconds
     */
    getDuration: function () {
        const player = this.state.videoPlayer;
        return player ? player.duration() : 0;
    },

    /**
     * Log an event
     *
     * @param {String} eventName - The name of the event to log
     * @param {Object} data - Additional data to log with the event
     */
    log: function (eventName, data) {
        const logInfo = _.extend(
            {
                host_component_id: this.state.id,
                bumper_id: this.state.config.sources[0] || '',
                duration: this.getDuration(),
                code: 'html5',
            },
            data,
            this.options.data
        );

        Logger.log(eventName, logInfo);
    },
};

export { VideoEventsBumperPlugin };