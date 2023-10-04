(function(define) {
    // eslint-disable-next-line lines-around-directive
    'use strict';

    // VideoTranscriptFeedbackHandler module.
    define(
        'video/037_video_transcript_feedback.js', ['underscore'],
        function(_) {
            var VideoTranscriptFeedbackHandler;

            /**
             * Video Transcript Feedback control module.
             * @exports video/037_video_transcript_feedback.js
             * @constructor
             * @param {jquery Element} element
             * @param {Object} options
             */
            VideoTranscriptFeedbackHandler = function(element, options) {
                if (!(this instanceof VideoTranscriptFeedbackHandler)) {
                    return new VideoTranscriptFeedbackHandler(element, options);
                }

                _.bindAll(this, 'sendPositiveFeedback');
                _.bindAll(this, 'sendNegativeFeedback');

                this.container = element;

                if (this.container.find('.wrapper-downloads .wrapper-transcript-feedback')) {
                    this.initialize();
                }

                return false;
            };

            VideoTranscriptFeedbackHandler.prototype = {

                // Initializes the module.
                initialize: function() {
                    this.el = this.container.find('.wrapper-transcript-feedback');
                    this.thumbsUpButton = this.el.find('.thumbs-up-btn');
                    this.thumbsDownButton = this.el.find('.thumbs-down-btn');
                    this.thumbsUpButton.on('click', this.sendPositiveFeedback);
                    this.thumbsDownButton.on('click', this.sendNegativeFeedback);
                },

                sendPositiveFeedback: function() {
                    this.thumbsUpIcon = this.thumbsUpButton.find('.thumbs-up-icon');
                    if (this.thumbsUpIcon[0].classList.contains('fa-thumbs-o-up')) {
                        this.thumbsUpIcon[0].classList.remove("fa-thumbs-o-up");
                        this.thumbsUpIcon[0].classList.add("fa-thumbs-up");
                    } else {
                        this.thumbsUpIcon[0].classList.remove("fa-thumbs-up");
                        this.thumbsUpIcon[0].classList.add("fa-thumbs-o-up");
                    }
                    // Send request
                },

                sendNegativeFeedback: function() {
                    this.thumbsDownIcon = this.thumbsDownButton.find('.thumbs-down-icon');
                    if (this.thumbsDownIcon[0].classList.contains('fa-thumbs-o-down')) {
                        this.thumbsDownIcon[0].classList.remove("fa-thumbs-o-down");
                        this.thumbsDownIcon[0].classList.add("fa-thumbs-down");
                    } else {
                        this.thumbsDownIcon[0].classList.remove("fa-thumbs-down");
                        this.thumbsDownIcon[0].classList.add("fa-thumbs-o-down");
                    }
                    // Send request
                },
            };

            return VideoTranscriptFeedbackHandler;
        });
}(RequireJS.define));
