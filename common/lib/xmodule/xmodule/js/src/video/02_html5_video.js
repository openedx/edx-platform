/**
 * @file HTML5 video player module. Provides methods to control the in-browser
 * HTML5 video player.
 *
 * The goal was to write this module so that it closely resembles the YouTube
 * API. The main reason for this is because initially the edX video player
 * supported only YouTube videos. When HTML5 support was added, for greater
 * compatibility, and to reduce the amount of code that needed to be modified,
 * it was decided to write a similar API as the one provided by YouTube.
 *
 * @external RequireJS
 *
 * @module HTML5Video
 */

(function (requirejs, require, define) {

define(
'video/02_html5_video.js',
[],
function () {
    var HTML5Video = {};

    HTML5Video.Player = (function () {
        Player.prototype.callStateChangeCallback = function () {
            if ($.isFunction(this.config.events.onStateChange)) {
                this.config.events.onStateChange({
                    data: this.playerState
                });
            }
        };

        Player.prototype.pauseVideo = function () {
            this.video.pause();
        };

        Player.prototype.seekTo = function (value) {
            if (
                typeof value === 'number' &&
                value <= this.video.duration &&
                value >= 0
            ) {
                this.video.currentTime = value;
            }
        };

        Player.prototype.setVolume = function (value) {
            if (typeof value === 'number' && value <= 100 && value >= 0) {
                this.video.volume = value * 0.01;
            }
        };

        Player.prototype.getCurrentTime = function () {
            return this.video.currentTime;
        };

        Player.prototype.playVideo = function () {
            this.video.play();
        };

        Player.prototype.getPlayerState = function () {
            return this.playerState;
        };

        Player.prototype.getVolume = function () {
            return this.video.volume;
        };

        Player.prototype.getDuration = function () {
            if (isNaN(this.video.duration)) {
                return 0;
            }

            return this.video.duration;
        };

        Player.prototype.setPlaybackRate = function (value) {
            var newSpeed;

            newSpeed = parseFloat(value);

            if (isFinite(newSpeed)) {
                if (this.video.playbackRate !== value) {
                    this.video.playbackRate = value;
                }
            }
        };

        Player.prototype.getAvailablePlaybackRates = function () {
            return [0.75, 1.0, 1.25, 1.5];
        };

        Player.prototype._getLogs = function () {
            return this.logs;
        };

        Player.prototype.showErrorMessage = function () {
            this.el
                .find('.video-player div')
                    .addClass('hidden')
                .end()
                .find('.video-player h3')
                    .removeClass('hidden')
                .end()
                    .addClass('is-initialized')
                .find('.spinner')
                    .attr({
                        'aria-hidden': 'true',
                        'tabindex': -1
                    });
        };

        Player.prototype.onError = function (event) {
            if ($.isFunction(this.config.events.onError)) {
                this.config.events.onError();
            }
        };

        Player.prototype.destroy = function () {
            this.video.removeEventListener('loadedmetadata', this.onLoadedMetadata, false);
            this.video.removeEventListener('play', this.onPlay, false);
            this.video.removeEventListener('playing', this.onPlaying, false);
            this.video.removeEventListener('pause', this.onPause, false);
            this.video.removeEventListener('ended', this.onEnded, false);
            this.el
                .find('.video-player div').removeClass('hidden')
                .end()
                .find('.video-player h3').addClass('hidden')
                .end().removeClass('is-initialized')
                .find('.spinner').attr({'aria-hidden': 'false'});
            this.videoEl.remove();
        };

        Player.prototype.onLoadedMetadata = function () {
            this.playerState = HTML5Video.PlayerState.PAUSED;
            if ($.isFunction(this.config.events.onReady)) {
                this.config.events.onReady(null);
            }
        };

        Player.prototype.onPlay = function () {
            this.playerState = HTML5Video.PlayerState.BUFFERING;
            this.callStateChangeCallback();
        };

        Player.prototype.onPlaying = function () {
            this.playerState = HTML5Video.PlayerState.PLAYING;
            this.callStateChangeCallback();
        };

        Player.prototype.onPause = function () {
            this.playerState = HTML5Video.PlayerState.PAUSED;
            this.callStateChangeCallback();
        };

        Player.prototype.onEnded = function () {
            this.playerState = HTML5Video.PlayerState.ENDED;
            this.callStateChangeCallback();
        };

        return Player;

        /*
         * Constructor function for HTML5 Video player.
         *
         * @param {String|Object} el A DOM element where the HTML5 player will
         * be inserted (as returned by jQuery(selector) function), or a
         * selector string which will be used to select an element. This is a
         * required parameter.
         *
         * @param config - An object whose properties will be used as
         * configuration options for the HTML5 video player. This is an
         * optional parameter. In the case if this parameter is missing, or
         * some of the config object's properties are missing, defaults will be
         * used. The available options (and their defaults) are as
         * follows:
         *
         *     config = {
         *
         *        videoSources: [],   // An array with properties being video
         *                            // sources. The property name is the
         *                            // video format of the source. Supported
         *                            // video formats are: 'mp4', 'webm', and
         *                            // 'ogg'.
         *
         *          events: {         // Object's properties identify the
         *                            // events that the API fires, and the
         *                            // functions (event listeners) that the
         *                            // API will call when those events occur.
         *                            // If value is null, or property is not
         *                            // specified, then no callback will be
         *                            // called for that event.
         *
         *              onReady: null,
         *              onStateChange: null
         *          }
         *     }
         */
        function Player(el, config) {
            var isTouch = onTouchBasedDevice() || '',
                sourceList, _this, errorMessage, lastSource;

            _.bindAll(this, 'onLoadedMetadata', 'onPlay', 'onPlaying', 'onPause', 'onEnded');
            this.logs = [];
            // Initially we assume that el is a DOM element. If jQuery selector
            // fails to select something, we assume that el is an ID of a DOM
            // element. We try to select by ID. If jQuery fails this time, we
            // return. Nothing breaks because the player 'onReady' event will
            // never be fired.

            this.el = $(el);
            if (this.el.length === 0) {
                this.el = $('#' + el);

                if (this.el.length === 0) {
                    errorMessage = gettext('VideoPlayer: Element corresponding to the given selector was not found.');
                    if (window.console && console.log) {
                        console.log(errorMessage);
                    } else {
                        throw new Error(errorMessage);
                    }
                    return;
                }
            }

            // A simple test to see that the 'config' is a normal object.
            if ($.isPlainObject(config)) {
                this.config = config;
            } else {
                return;
            }

            // We should have at least one video source. Otherwise there is no
            // point to continue.
            if (!config.videoSources && !config.videoSources.length) {
                return;
            }


            // Will be used in inner functions to point to the current object.
            _this = this;

            // Create HTML markup for individual sources of the HTML5 <video>
            // element.
            sourceList = $.map(config.videoSources, function (source) {
               return [
                    '<source ',
                        'src="', source,
            // Following hack allows to open the same video twice
            // https://code.google.com/p/chromium/issues/detail?id=31014
            // Check whether the url already has a '?' inside, and if so,
            // use '&' instead of '?' to prevent breaking the url's integrity.
                        (source.indexOf('?') === -1 ? '?' : '&'),
                        (new Date()).getTime(), '" />'
                ].join('');
            });


            // Create HTML markup for the <video> element, populating it with
            // sources from previous step. Because of problems with creating
            // video element via jquery (http://bugs.jquery.com/ticket/9174) we
            // create it using native JS.
            this.video = document.createElement('video');

            errorMessage = [
                gettext('This browser cannot play .mp4, .ogg, or .webm files.'),
                gettext('Try using a different browser, such as Google Chrome.')
            ].join('');
            this.video.innerHTML = sourceList.join('') + errorMessage;

            // Get the jQuery object, and set the player state to UNSTARTED.
            // The player state is used by other parts of the VideoPlayer to
            // determine what the video is currently doing.
            this.videoEl = $(this.video);

            lastSource = this.videoEl.find('source').last();
            lastSource.on('error', this.showErrorMessage.bind(this));
            lastSource.on('error', this.onError.bind(this));
            this.videoEl.on('error', this.onError.bind(this));

            if (/iP(hone|od)/i.test(isTouch[0])) {
                this.videoEl.prop('controls', true);
            }

            this.playerState = HTML5Video.PlayerState.UNSTARTED;

            // Attach a 'click' event on the <video> element. It will cause the
            // video to pause/play.
            this.videoEl.on('click', function (event) {
                var PlayerState = HTML5Video.PlayerState;

                if (_this.playerState === PlayerState.PLAYING) {
                    _this.playerState = PlayerState.PAUSED;
                    _this.pauseVideo();
                } else {
                    _this.playerState = PlayerState.PLAYING;
                    _this.playVideo();
                }
            });

            var events = ['loadstart', 'progress', 'suspend', 'abort', 'error',
                'emptied', 'stalled', 'play', 'pause', 'loadedmetadata',
                'loadeddata', 'waiting', 'playing', 'canplay', 'canplaythrough',
                'seeking', 'seeked', 'timeupdate', 'ended', 'ratechange',
                'durationchange', 'volumechange'
            ];

            this.debug = false;
            $.each(events, function(index, eventName) {
                _this.video.addEventListener(eventName, function () {
                    _this.logs.push({
                        'event name': eventName,
                        'state': _this.playerState
                    });

                    if (_this.debug) {
                        console.log(
                            'event name:', eventName,
                            'state:', _this.playerState,
                            'readyState:', _this.video.readyState,
                            'networkState:', _this.video.networkState
                        );
                    }

                    el.trigger('html5:' + eventName, arguments);
                });
            });

            // When the <video> tag has been processed by the browser, and it
            // is ready for playback, notify other parts of the VideoPlayer,
            // and initially pause the video.
            this.video.addEventListener('loadedmetadata', this.onLoadedMetadata, false);
            this.video.addEventListener('play', this.onPlay, false);
            this.video.addEventListener('playing', this.onPlaying, false);
            this.video.addEventListener('pause', this.onPause, false);
            this.video.addEventListener('ended', this.onEnded, false);

            // Place the <video> element on the page.
            this.videoEl.appendTo(this.el.find('.video-player div'));
        }
    }());

    // The YouTube API presents several constants which describe the player's
    // state at a given moment. HTML5Video API will copy these constants so
    // that code which uses both the YouTube API and this API doesn't have to
    // change.
    HTML5Video.PlayerState = {
        UNSTARTED: -1,
        ENDED: 0,
        PLAYING: 1,
        PAUSED: 2,
        BUFFERING: 3,
        CUED: 5
    };

    // HTML5Video object - what this module exports.
    return HTML5Video;
});

}(RequireJS.requirejs, RequireJS.require, RequireJS.define));
