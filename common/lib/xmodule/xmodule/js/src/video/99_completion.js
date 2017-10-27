(function(define) {
    'use strict';
    define('video/99_completion.js', [], function() {
    /**
     * Play/pause control module.
     * @exports video/09_play_pause_control.js
     * @constructor
     * @param {Object} state The object containing the state of the video
     * @return {jquery Promise}
     */
        var VideoCompletionHandler = function(state) {
            if (!(this instanceof VideoCompletionHandler)) {
                return new VideoCompletionHandler(state);
            }

            _.bindAll(this, 'play', 'pause', 'onClick', 'destroy');
            this.state = state;
            this.state.completionHandler = this;
            this.initialize();

            return $.Deferred().resolve().promise();
        };

        VideoCompletionHandler.prototype = {
            destroy: function() {
                this.el.remove();
                this.state.el.off('destroy', this.destroy);
                delete this.state.videoPlayPauseControl;
            },

        /** Initializes the module. */
            initialize: function() {
                this.complete = false;
                this.lastValue = 1;
                this.bindHandlers();
            },

        /** Bind any necessary function callbacks to DOM events. */
            bindHandlers: function() {
                this.state.el.on({timeupdate: this.checkCompletion});
            },

        /** Event handler to check if the video is complete, and submit a completion if it is */
            checkCompletion: function(currentTime) {
                // Need to access runtime for this.
                if (currentTime != this.lastValue) {
                    console.warn("CURRENT TIME", currentTime);
                    this.lastValue = currentTime;
                }
                if (this.complete === false && currentTime > this.state.completeAfter) {
                    this.complete = true;
                    if (this.state.config.publishCompletionUrl) {
                        $.ajax({
                            type: 'POST',
                            url: this.state.config.publishCompletionUrl,
                            data: JSON.stringify({
                                completion: 1.0
                            })
                        });
                    } else {
                        console.warn('publishCompletionUrl not defined');
                    }
                }
            }
        };

        return VideoCompletionHandler;
    });
}(RequireJS.define));
