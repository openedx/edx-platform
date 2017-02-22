/* eslint-disable no-console, no-param-reassign */
/**
 * HTML5 video player module to support HLS video playback.
 *
 */

(function(requirejs, require, define) {
    'use strict';
    define('video/02_html5_hls_video.js', ['video/02_html5_video.js', 'hls'], function(HTML5Video, HLS) {
        var HLSVideo = {};

        HLSVideo.Player = (function() {
            function PlayerHLS(el, config) {
                var self = this;

                // do common initialization independent of player type
                this.init(el, config);

                // Safari has native support to play HLS videos
                if (config.browserIsSafari) {
                    this.videoEl.attr('src', config.videoSources[0]);
                } else {
                    this.hls = new HLS();
                    this.hls.attachMedia(this.video);
                    this.hls.on(HLS.Events.ERROR, this.onError.bind(this));
                    this.hls.on(HLS.Events.MEDIA_ATTACHED, function() {
                        self.hls.loadSource(config.videoSources[0]);
                        self.hls.on(HLS.Events.MANIFEST_PARSED, function(event, data) {
                            console.log(
                                '[HLS Video]: Manifest loaded, found ' + data.levels.length + ' quality level'
                            );
                        });
                    });
                }
            }

            PlayerHLS.prototype = Object.create(HTML5Video.Player.prototype);
            PlayerHLS.prototype.constructor = PlayerHLS;

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
