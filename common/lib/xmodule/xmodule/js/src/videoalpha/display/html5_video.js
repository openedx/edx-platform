this.HTML5Video = (function () {
    var HTML5Video = {};

    HTML5Video.Player = (function () {

        /*
         * Constructor function for HTML5 Video player.
         *
         * @el - A DOM element where the HTML5 player will be inserted (as returned by jQuery(selector) function),
         * or a selector string which will be used to select an element. This is a required parameter.
         *
         * @config - An object whose properties will be used as configuration options for the HTML5 video
         * player. This is an optional parameter. In the case if this parameter is missing, or some of the config
         * object's properties are missing, defaults will be used. The available options (and their defaults) are as
         * follows:
         *
         *     config = {
         *
         *         'videoSources': {},   // An object of with properties being video sources. The property name is the
         *                               // video format of the source. Supported video formats are: 'mp4', 'webm', and
         *                               // 'ogg'. By default videoSources property is null. This means that the
         *                               // player will initialize, and not play anything. If you do not provide a
         *                               // 'videoSource' option, you can later call loadVideoBySource() method to load
         *                               // a video and start playing it.
         *
         *          'playerVars': {     // Object's properties identify player parameters.         *
         *              'start': null,  // Possible values: positive integer. Position from which to start playing the
         *                              // video. Measured in seconds. If value is null, or 'start' property is not
         *                              // specified, the video will start playing from the beginning.
         *
         *              'end': null     // Possible values: positive integer. Position when to stop playing the
         *                              // video. Measured in seconds. If value is null, or 'end' property is not
         *                              // specified, the video will end playing at the end.
         *
         *          },
         *
         *          'events': {         // Object's properties identify the events that the API fires, and the
         *                              // functions (event listeners) that the API will call when those events occur.
         *                              // If value is null, or property is not specified, then no callback will be
         *                              // called for that event.
         *
         *              'onReady': null,
         *              'onStateChange': null
         *          }
         *     }
         */
        function Player(el, config) {
            var sourceStr, _this;

            if (typeof el === 'string') {
                this.el = $(el);
            } else if (el instanceof jQuery) {
                this.el = el;
            } else {
                // Error. Parameter el does not have a recognized type.

                // TODO: Make sure that nothing breaks if one of the methods available via this object's prototype
                // is called after we return.

                return;
            }

            if ($.isPlainObject(config) === true) {
                this.config = config;
            } else {
                // Error. Parameter config does not have a recognized type.

                // TODO: Make sure that nothing breaks if one of the methods available via this object's prototype
                // is called after we return.

                return;
            }

            this.start = 0;
            this.end = null;
            if (config.hasOwnProperty('playerVars') === true) {
                this.start = parseFloat(config.playerVars.start);
                if ((isFinite(this.start) !== true) || (this.start < 0)) {
                    this.start = 0;
                }

                this.end = parseFloat(config.playerVars.end);
                if ((isFinite(this.end) !== true) || (this.end < this.start)) {
                    this.end = null;
                }
            }

            sourceStr = {
                'mp4': ' ',
                'webm': ' ',
                'ogg': ' '
            };

            _this = this;
            $.each(sourceStr, function (videoType, videoSource) {
                if (
                    (_this.config.videoSources.hasOwnProperty(videoType) === true) &&
                    (typeof _this.config.videoSources[videoType] === 'string') &&
                    (_this.config.videoSources[videoType].length > 0)
                ) {
                    sourceStr[videoType] =
                        '<source ' +
                            'src="' + _this.config.videoSources[videoType] + '" ' +
                            'type="video/' + videoType + '" ' +
                        '/> ';
                }
            });

            this.playerState = HTML5Video.PlayerState.UNSTARTED;

            this.videoEl = $(
                '<video style="width: 100%;">' +
                    sourceStr.mp4 +
                    sourceStr.webm +
                    sourceStr.ogg +
                '</video>'
            );

            this.video = this.videoEl[0];

            this.videoEl.on('click', function (event) {
                if (_this.playerState === HTML5Video.PlayerState.PAUSED) {
                    _this.video.play();
                    _this.playerState = HTML5Video.PlayerState.PLAYING;

                    if ($.isFunction(_this.config.events.onStateChange) === true) {
                        _this.config.events.onStateChange({
                            'data': _this.playerState
                        });
                    }
                } else if (_this.playerState === HTML5Video.PlayerState.PLAYING) {
                    _this.video.pause();
                    _this.playerState = HTML5Video.PlayerState.PAUSED;

                    if ($.isFunction(_this.config.events.onStateChange) === true) {
                        _this.config.events.onStateChange({
                            'data': _this.playerState
                        });
                    }
                }
            });

            this.video.addEventListener('canplay', function () {
                _this.playerState = HTML5Video.PlayerState.PAUSED;

                if (_this.start > _this.video.duration) {
                    _this.start = 0;
                }
                if ((_this.end === null) || (_this.end > _this.video.duration)) {
                    _this.end = _this.video.duration;
                }
                _this.video.currentTime = _this.start;

                if ($.isFunction(_this.config.events.onReady) === true) {
                    _this.config.events.onReady({});
                }
            }, false);
            this.video.addEventListener('play', function () {
                _this.playerState = HTML5Video.PlayerState.PLAYING;

                if ($.isFunction(_this.config.events.onStateChange) === true) {
                    _this.config.events.onStateChange({
                        'data': _this.playerState
                    });
                }
            }, false);
            this.video.addEventListener('pause', function () {
                _this.playerState = HTML5Video.PlayerState.PAUSED;

                if ($.isFunction(_this.config.events.onStateChange) === true) {
                    _this.config.events.onStateChange({
                        'data': _this.playerState
                    });
                }
            }, false);
            this.video.addEventListener('ended', function () {
                _this.playerState = HTML5Video.PlayerState.ENDED;

                if ($.isFunction(_this.config.events.onStateChange) === true) {
                    _this.config.events.onStateChange({
                        'data': _this.playerState
                    });
                }
            }, false);
            this.video.addEventListener('timeupdate', function (data) {
                console.log('[timeupdate]');
                console.log(_this.video.currentTime);
                if (_this.video.end > _this.video.currentTime) {
                    console.log('_this.video.end >= _this.video.currentTime -> pausing video');
                    _this.playerState = HTML5Video.PlayerState.PAUSED;

                    if ($.isFunction(_this.config.events.onStateChange) === true) {
                        _this.config.events.onStateChange({
                            'data': _this.playerState
                        });
                    }
                }
            }, false);

            this.videoEl.appendTo(this.el.find('.video-player div'));
        }

        Player.prototype.pauseVideo = function () {
            this.video.pause();
        };

        Player.prototype.seekTo = function (value) {
            if ((typeof value === 'number') && (value <= this.video.duration) && (value >= 0)) {
                this.video.currentTime = value;
            }
        };

        Player.prototype.setVolume = function (value) {
            if ((typeof value === 'number') && (value <= 100) && (value >= 0)) {
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
            return this.video.duration;
        };

        Player.prototype.setSpeed = function (value) {
            var newSpeed;

            newSpeed = parseFloat(value);

            if (isFinite(newSpeed) === true) {
                this.video.playbackRate = value;
            }
        };

        Player.prototype.getAvailablePlaybackRates = function () {
            return [0.75, 1.0, 1.25, 1.5];
        };

        return Player;
    }());

    HTML5Video.PlayerState = {
        'UNSTARTED': -1,
        'ENDED': 0,
        'PLAYING': 1,
        'PAUSED': 2,
        'BUFFERING': 3,
        'CUED': 5
    };

    return HTML5Video;
}());
