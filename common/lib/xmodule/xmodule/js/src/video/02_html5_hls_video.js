/* eslint-disable no-console, no-param-reassign */
/**
 * HTML5 video player module to support HLS video playback.
 *
 */

(function(requirejs, require, define) {
    'use strict';
    define('video/02_html5_hls_video.js', ['video/02_html5_video.js', 'hls', 'underscore'],
    function(HTML5Video, HLS, _) {
        var HLSVideo = {};

        HLSVideo.Player = (function() {
            function PlayerHLS(el, config) {
                var self = this;

                // do common initialization independent of player type
                this.init(el, config);

                // If we have only HLS sources and browser doesn't support HLS
                // then show error message.
                if (config.HLSOnlySources && !config.canPlayHLS) {
                    this.showErrorMessage();
                    return;
                }

                // Safari has native support to play HLS videos
                if (config.browserIsSafari) {
                    this.videoEl.attr('src', config.videoSources[0]);
                } else {
                    this.hls = new HLS();
                    this.hls.loadSource(config.videoSources[0]);
                    this.hls.attachMedia(this.video);
                    this.hls.on(HLS.Events.ERROR, this.onError.bind(this));
                    this.hls.on(HLS.Events.MANIFEST_PARSED, function(event, data) {
                        console.log(
                            '[HLS Video]: MANIFEST_PARSED, qualityLevelsInfo: ',
                            data.levels.map(function(level) {
                                return {
                                    url: level.url[0],
                                    bitrate: level.bitrate,
                                    resolution: level.width + 'x' + level.height
                                };
                            })
                        );
                    });
                    this.hls.on(HLS.Events.LEVEL_SWITCHING, function(event, data) {
                        console.log('[HLS Video]: LEVEL_SWITCHING, levelId: ', data.level);
                    });
                    this.hls.on(HLS.Events.LEVEL_SWITCHED, function(event, data) {
                        var level = self.hls.levels[data.level];
                        console.log(
                            '[HLS Video]: LEVEL_SWITCHED, qualityLevelInfo: ',
                            {
                                levelId: data.level,
                                url: level.url[0],
                                bitrate: level.bitrate,
                                resolution: level.width + 'x' + level.height
                            }
                        );
                    });
                }
            }

            PlayerHLS.prototype = Object.create(HTML5Video.Player.prototype);
            PlayerHLS.prototype.constructor = PlayerHLS;

            PlayerHLS.prototype.showErrorMessage = function() {
                this.el
                    .find('.video-player div')
                    .addClass('hidden')
                    .end()
                    .find('.video-player .video-hls-error')
                    .removeClass('is-hidden')
                    .end()
                    .addClass('is-initialized')
                    .find('.spinner')
                    .attr({
                        'aria-hidden': 'true',
                        tabindex: -1
                    });
            };

            PlayerHLS.prototype.onError = function(event, data) {
                if (data.fatal) {
                    switch (data.type) {
                    case HLS.ErrorTypes.NETWORK_ERROR:
                        console.error(
                            '[HLS Video]: Fatal network error encountered, try to recover. Details: %s',
                            data.details
                        );
                        this.hls.startLoad();
                        break;
                    case HLS.ErrorTypes.MEDIA_ERROR:
                        console.error(
                            '[HLS Video]: Fatal media error encountered, try to recover. Details: %s',
                            data.details
                        );
                        this.hls.recoverMediaError();
                        break;
                    default:
                        console.error(
                            '[HLS Video]: Unrecoverable error encountered. Details: %s',
                            data.details
                        );
                        break;
                    }
                }
            };

            return PlayerHLS;
        }());

        return HLSVideo;
    });
}(RequireJS.requirejs, RequireJS.require, RequireJS.define));
