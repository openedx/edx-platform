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

                _.bindAll(this,  'destroy', 'getFeedbackForCurrentTranscript', 'markAsPositiveFeedback', 'markAsNegativeFeedback', 'markAsEmptyFeedback',
                    'selectThumbsUp', 'selectThumbsDown', 'unselectThumbsUp', 'unselectThumbsDown', 'thumbsUpClickHandler', 'thumbsDownClickHandler',
                    'onHideLanguageMenu', 'getCurrentLanguage', 'instantiateWidget', 'shouldShowWidget', 'showWidget', 'hideWidget'
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

                    this.videoId = this.el.data('video-id');
                    this.userId = this.el.data('user-id');
                    // this.aiTranslationsUrl = this.state.config.getFeedbackUrl;
                    this.aiTranslationsUrl = 'http://localhost:18760/api/v1';

                    this.thumbsUpButton = this.el.find('.thumbs-up-btn');
                    this.thumbsDownButton = this.el.find('.thumbs-down-btn');
                    this.thumbsUpButton.on('click', this.thumbsUpClickHandler);
                    this.thumbsDownButton.on('click', this.thumbsDownClickHandler);

                    this.events = {
                        'language_menu:hide': this.onHideLanguageMenu,
                        destroy: this.destroy
                    };
                    this.instantiateWidget();
                    this.bindHandlers();
                },

                bindHandlers: function() {
                    this.state.el.on(this.events);
                },

                getFeedbackForCurrentTranscript: function() {
                    var self = this;
                    var url = this.aiTranslationsUrl + '/transcript-feedback' + '?transcript_language=' + this.currentTranscriptLanguage + '&video_uuid=' + this.videoId + '&user_id=' + this.userId;

                    $.ajax({
                        url: url,
                        type: 'GET',
                    })
                    .success(function(data) {
                        if (data && data.value === true) {
                            self.markAsPositiveFeedback();
                            self.currentFeedback = true;
                        } else {
                            if (data && data.value === false) {
                                self.markAsNegativeFeedback();
                                self.currentFeedback = false;
                            } else {
                                self.markAsEmptyFeedback();
                                self.currentFeedback = null;
                            }
                        }
                    });
                },

                markAsPositiveFeedback: function() {
                    this.selectThumbsUp();
                    this.unselectThumbsDown();
                },

                markAsNegativeFeedback: function() {
                    this.selectThumbsDown();
                    this.unselectThumbsUp();
                },

                markAsEmptyFeedback: function() {
                    this.unselectThumbsUp();
                    this.unselectThumbsDown();
                },

                selectThumbsUp: function() {
                    var thumbsUpIcon = this.thumbsUpButton.find('.thumbs-up-icon');
                    if (thumbsUpIcon[0].classList.contains('fa-thumbs-o-up')) {
                        thumbsUpIcon[0].classList.remove("fa-thumbs-o-up");
                        thumbsUpIcon[0].classList.add("fa-thumbs-up");
                    }
                },

                selectThumbsDown: function() {
                    var thumbsDownIcon = this.thumbsDownButton.find('.thumbs-down-icon');
                    if (thumbsDownIcon[0].classList.contains('fa-thumbs-o-down')) {
                        thumbsDownIcon[0].classList.remove("fa-thumbs-o-down");
                        thumbsDownIcon[0].classList.add("fa-thumbs-down");
                    }
                },

                unselectThumbsUp: function() {
                    var thumbsUpIcon = this.thumbsUpButton.find('.thumbs-up-icon');
                    if (thumbsUpIcon[0].classList.contains('fa-thumbs-up')) {
                        thumbsUpIcon[0].classList.remove("fa-thumbs-up");
                        thumbsUpIcon[0].classList.add("fa-thumbs-o-up");
                    }
                },

                unselectThumbsDown: function() {
                    var thumbsDownIcon = this.thumbsDownButton.find('.thumbs-down-icon');
                    if (thumbsDownIcon[0].classList.contains('fa-thumbs-down')) {
                        thumbsDownIcon[0].classList.remove("fa-thumbs-down");
                        thumbsDownIcon[0].classList.add("fa-thumbs-o-down");
                    }
                },

                thumbsUpClickHandler: function() {
                    if (this.currentFeedback) {
                        // Send request with null
                        this.markAsEmptyFeedback();
                    } else {
                        // Send request with true
                        this.markAsPositiveFeedback();
                    }
                },

                thumbsDownClickHandler: function() {
                    if (this.currentFeedback === false) {
                        // Send request with null
                        this.markAsEmptyFeedback();
                    } else {
                        // Send request with false
                        this.markAsNegativeFeedback();
                    }
                },

                onHideLanguageMenu: function() {
                    var newLanguageSelected = this.getCurrentLanguage();
                    if (this.currentTranscriptLanguage !== newLanguageSelected) {
                        this.currentTranscriptLanguage = this.getCurrentLanguage();
                        this.instantiateWidget();
                    }
                },

                getCurrentLanguage: function() {
                    var language = this.state.lang;
                    return language;
                },

                instantiateWidget: function() {
                    var self = this;
                    $.when(this.shouldShowWidget()).done(function(shouldShowWidget) {
                        if (shouldShowWidget) {
                            self.showWidget();
                            self.getFeedbackForCurrentTranscript();
                        } else {
                            self.hideWidget();
                        }
                    })
                },

                shouldShowWidget: function() {
                    var url = this.aiTranslationsUrl + '/video-transcript' + '?transcript_language=' + this.currentTranscriptLanguage + '&video_uuid=' + this.videoId;

                    return $.ajax({
                        url: url,
                        type: 'GET',
                        async: false,
                    })
                    .success(function(data) {
                        return (data && data.status === 'Completed')
                    });
                },

                showWidget: function() {
                    this.el.show();
                },

                hideWidget: function() {
                    this.el.hide();
                },

            };

            return VideoTranscriptFeedbackHandler;
        });
}(RequireJS.define));
