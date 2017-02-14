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
                    this.hls.on(HLS.Events.MEDIA_ATTACHED, function() {
                        self.hls.loadSource(config.videoSources[0]);
                        self.hls.on(HLS.Events.MANIFEST_PARSED, function(event, data) {
                            console.log(
                                '[Video info]: manifest loaded, found ' + data.levels.length + ' quality level'
                            );
                        });
                    });
                }
            }

            PlayerHLS.prototype = Object.create(HTML5Video.Player.prototype);
            PlayerHLS.prototype.constructor = PlayerHLS;

            return PlayerHLS;
        }());

        return HLSVideo;
    });
}(RequireJS.requirejs, RequireJS.require, RequireJS.define));
