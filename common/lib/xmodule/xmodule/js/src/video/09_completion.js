(function(define) {
    'use strict';
    /**
     * Completion handler
     * @exports video/09_completion.js
     * @constructor
     * @param {Object} state The object containing the state of the video
     * @return {jquery Promise}
     */
    define('video/09_completion.js', [], function() {
        var VideoCompletionHandler = function(state) {
            if (!(this instanceof VideoCompletionHandler)) {
                return new VideoCompletionHandler(state);
            }
            this.state = state;
            this.state.completionHandler = this;
            this.initialize();
            return $.Deferred().resolve().promise();
        };

        VideoCompletionHandler.prototype = {

            /** Tears down the VideoCompletionHandler.
             *
             *  * Removes backreferences from this.state to this.
             *  * Turns off signal handlers.
             */
            destroy: function() {
                this.el.remove();
                this.el.off('timeupdate.completion');
                this.el.off('ended.completion');
                delete this.state.completionHandler;
            },

            /** Initializes the VideoCompletionHandler.
             *
             *  This sets all the instance variables needed to perform
             *  completion calculations.
             */
            initialize: function() {
                // Attributes with "Time" in the name refer to the number of seconds since
                // the beginning of the video, except for lastSentTime, which refers to a
                // timestamp in seconds since the Unix epoch.
                this.lastSentTime = undefined;
                this.lastProgressPercentage = undefined;
                this.isComplete = false;
                this.completionPercentage = this.state.config.completionPercentage;
                this.startTime = this.state.config.startTime;
                this.endTime = this.state.config.endTime;
                this.isEnabled = this.state.config.completionEnabled;
                if (this.endTime) {
                    this.completeAfterTime = this.calculateCompleteAfterTime(this.startTime, this.endTime);
                }
                if (this.isEnabled) {
                    this.bindHandlers();
                }
            },

            /** Bind event handler callbacks.
             *
             *  When ended is triggered, mark the video complete
             *  unconditionally.
             *
             *  When timeupdate is triggered, check to see if the user has
             *  passed the completeAfterTime in the video, and if so, mark the
             *  video complete.
             *
             *  When destroy is triggered, clean up outstanding resources.
             */
            bindHandlers: function() {
                var self = this;

                /** Event handler to check if the video is complete, and submit
                 *  a completion if it is.
                 *
                 *  If the timeupdate handler doesn't fire after the required
                 *  percentage, this will catch any fully complete videos.
                 */
                this.state.el.on('ended.completion', function() {
                    self.handleEnded();
                });

                /** Event handler to check video progress, and mark complete if
                 *  greater than completionPercentage
                 */
                this.state.el.on('timeupdate.completion', function(ev, currentTime) {
                    self.handleTimeUpdate(currentTime);
                });

                /** Event handler to clean up resources when the video player
                 *  is destroyed.
                 */
                this.state.el.off('destroy', this.destroy);
            },

            /** Handler to call when the ended event is triggered */
            handleEnded: function() {
                if (this.isComplete) {
                    return;
                }
                this.markCompletion();
            },

            /** Handler to call when a timeupdate event is triggered */
            handleTimeUpdate: function(currentTime) {
                var duration = this.state.videoPlayer.duration();
                if (this.isComplete) {
                    return;
                }
                if (this.lastSentTime !== undefined && currentTime - this.lastSentTime < this.repostDelaySeconds()) {
                    // Throttle attempts to submit in case of network issues
                    return;
                }

                // Duration may not be available at initialization time
                if (duration) {
                    this.computeProgress(currentTime, duration);
                }

                if (this.completeAfterTime === undefined) {
                    // Duration is not available at initialization time
                    duration = this.state.videoPlayer.duration();
                    if (!duration) {
                        // duration is not yet set. Wait for another event,
                        // or fall back to 'ended' handler.
                        return;
                    }
                    this.completeAfterTime = this.calculateCompleteAfterTime(this.startTime, duration);
                }

                if (currentTime > this.completeAfterTime) {
                    this.markCompletion(currentTime);
                }
            },

            /** Compute current video progression and trigger event if needed */
            computeProgress: function(currentTime, duration) {
                // Compute current progress percentage
                var currentProgressPercentage = Math.floor(currentTime * 100 / duration / 5) * 5;
                // Check if last "lastProgressPercentage" and current percentage are in the same 5-range
                var newRange = currentProgressPercentage > this.lastProgressPercentage;
                // If no previous "lastProgressPercentage" or different 5-range, trigger the event
                if (this.lastProgressPercentage === undefined || newRange) {
                    this.triggerProgress(Math.floor(currentProgressPercentage));
                    // Save the lastProgressPercentage value
                    this.lastProgressPercentage = currentProgressPercentage;
                }
            },

            /** Trigger progress event */
            triggerProgress: function(percentage) {
                this.state.el.trigger('progress', [percentage]);
            },

            /** Submit completion to the LMS */
            markCompletion: function(currentTime) {
                var self = this;
                var errmsg;
                this.isComplete = true;
                this.lastSentTime = currentTime;
                if (this.state.config.publishCompletionUrl) {
                    $.ajax({
                        type: 'POST',
                        url: this.state.config.publishCompletionUrl,
                        contentType: 'application/json',
                        dataType: 'json',
                        data: JSON.stringify({completion: 1.0}),
                        success: function() {
                            self.state.el.off('timeupdate.completion');
                            self.state.el.off('ended.completion');
                        },
                        error: function(xhr) {
                            /* eslint-disable no-console */
                            self.complete = false;
                            errmsg = 'Failed to submit completion';
                            if (xhr.responseJSON !== undefined) {
                                errmsg += ': ' + xhr.responseJSON.error;
                            }
                            console.warn(errmsg);
                            /* eslint-enable no-console */
                        }
                    });
                } else {
                    /* eslint-disable no-console */
                    console.warn('publishCompletionUrl not defined');
                    /* eslint-enable no-console */
                }
            },

            /** Determine what point in the video (in seconds from the
             *  beginning) counts as complete.
             */
            calculateCompleteAfterTime: function(startTime, endTime) {
                return startTime + (endTime - startTime) * this.completionPercentage;
            },

            /** How many seconds to wait after a POST fails to try again. */
            repostDelaySeconds: function() {
                return 3.0;
            }
        };
        return VideoCompletionHandler;
    });
}(RequireJS.define));
