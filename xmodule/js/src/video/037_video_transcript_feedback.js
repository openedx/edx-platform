(function(define) {
    // VideoTranscriptFeedbackHandler module.

        'use strict';

        define('video/037_video_caption.js', ['underscore'],
        function(_) {
            /**
             * @desc VideoTranscriptFeedbackHandler module exports a function.
             *
             * @type {function}
             * @access public
             *
             * @param {object} state - The object containing the state of the video
             *     player. All other modules, their parameters, public variables, etc.
             *     are available via this object.
             *
             * @this {object} The global window object.
             *
             */

            var VideoTranscriptFeedbackHandler = function(state) {
                if (!(this instanceof VideoTranscriptFeedbackHandler)) {
                    return new VideoTranscriptFeedbackHandler(state);
                }

                _.bindAll(this, 'sendPositiveFeedback', 'sendNegativeFeedback', 'onHideLanguageMenu',
                    'destroy'
                );

                this.state = state;
                this.currentTranscriptLanguage = this.state.lang;
                this.transcriptLanguages = this.state.config.transcriptLanguages;

                if (this.state.el.find('.wrapper-downloads .wrapper-transcript-feedback')) {
                    this.initialize();
                }

                return false;
            };

            VideoTranscriptFeedbackHandler.prototype = {

                destroy: function() {
                    this.state.el.off(this.events);
                },

                // Initializes the module.
                initialize: function() {
                    this.el = this.state.el.find('.wrapper-transcript-feedback');

                    this.video_id = this.el.data('video-id');
                    this.user_id = this.el.data('user-id');

                    this.thumbsUpButton = this.el.find('.thumbs-up-btn');
                    this.thumbsDownButton = this.el.find('.thumbs-down-btn');
                    this.thumbsUpButton.on('click', this.sendPositiveFeedback);
                    this.thumbsDownButton.on('click', this.sendNegativeFeedback);

                    this.events = {
                        'language_menu:hide': this.onHideLanguageMenu,
                        destroy: this.destroy
                    };
                    this.bindHandlers();
                },

                bindHandlers: function() {
                    this.state.el.on(this.events);
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

                onHideLanguageMenu: function() {
                    this.currentTranscriptLanguage = this.getCurrentLanguage();
                },

                getCurrentLanguage: function() {
                    var language = this.state.lang;
                    return language;
                },
            };

            return VideoTranscriptFeedbackHandler;
        });
}(RequireJS.define));
