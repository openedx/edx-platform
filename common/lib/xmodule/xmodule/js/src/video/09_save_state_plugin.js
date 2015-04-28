(function(define) {
'use strict';
// VideoSaveStatePlugin module.
define(
'video/09_save_state_plugin.js', [],
function() {
    /**
     * Video volume control module.
     * @exports video/09_save_state_plugin.js
     * @constructor
     * @param {Object} state The object containing the state of the video
     * @param {Object} i18n The object containing strings with translations.
     * @return {jquery Promise}
     */
    var SaveStatePlugin = function(state, i18n, options) {
        if (!(this instanceof SaveStatePlugin)) {
            return new SaveStatePlugin(state, i18n, options);
        }

        _.bindAll(this, 'onSpeedChange', 'saveStateHandler', 'bindUnloadHandler', 'onUnload', 'onTranscriptDownload',
            'onYoutubeAvailability', 'onLanguageChange', 'destroy');
        this.state = state;
        this.options = _.extend({events: []}, options);
        this.state.videoSaveStatePlugin = this;
        this.i18n = i18n;
        this.initialize();

        return $.Deferred().resolve().promise();
    };


    SaveStatePlugin.moduleName = 'SaveStatePlugin';
    SaveStatePlugin.prototype = {
        destroy: function () {
            this.state.el.off({
                'speedchange': this.onSpeedChange,
                'play': this.bindUnloadHandler,
                'pause destroy': this.saveStateHandler,
                'transcript_download:change': this.onTranscriptDownload,
                'language_menu:change': this.onLanguageChange,
                'youtube_availability': this.onYoutubeAvailability,
                'destroy': this.destroy
            });
            $(window).off('unload', this.onUnload);
            delete this.state.videoSaveStatePlugin;
        },

        initialize: function() {
            this.bindHandlers();
        },

        bindHandlers: function() {
            var eventMapping = {
                'speedchange': this.onSpeedChange,
                'play': this.bindUnloadHandler,
                'pause destroy': this.saveStateHandler,
                'transcript_download:change': this.onTranscriptDownload,
                'language_menu:change': this.onLanguageChange,
                'youtube_availability': this.onYoutubeAvailability
            };

            if (this.options.events.length) {
                _.each(this.options.events, function (eventName) {
                    var callback;
                    if (_.has(eventMapping, eventName)) {
                        callback = eventMapping[eventName];
                        this.state.el.on(eventName, callback);
                    }
                }, this);
            } else {
                this.state.el.on(eventMapping);
            }
            this.state.el.on('destroy', this.destroy);
        },

        bindUnloadHandler: _.once(function () {
            $(window).on('unload.video', this.onUnload);
        }),

        onSpeedChange: function (event, newSpeed) {
            this.saveState(true, {speed: newSpeed});
            this.state.storage.setItem('speed', this.state.speed, true);
            this.state.storage.setItem('general_speed', this.state.speed);
        },

        saveStateHandler: function () {
            this.saveState(true);
        },

        onUnload: function () {
            this.saveState();
        },

        onTranscriptDownload: function (event, fileType) {
            this.saveState(true, {'transcript_download_format': fileType});
            this.state.storage.setItem('transcript_download_format', fileType);
        },

        onLanguageChange: function (event, langCode) {
            this.state.storage.setItem('language', langCode);
        },

        onYoutubeAvailability: function (event, youtubeIsAvailable) {
            this.saveState(true, {youtube_is_available: youtubeIsAvailable});
        },

        saveState: function (async, data) {
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
                async: async ? true : false,
                dataType: 'json',
                data: data
            });
        }
    };

    return SaveStatePlugin;
});
}(RequireJS.define));
