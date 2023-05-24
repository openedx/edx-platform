(function(define) {
    'use strict';

    // VideoSocialSharingHandler module.
    define(
        'video/036_video_social_sharing.js', ['underscore'],
        function(_) {
            var VideoSocialSharingHandler;

            /**
             * Video Social Sharing control module.
             * @exports video/036_video_social_sharing.js
             * @constructor
             * @param {jquery Element} element
             * @param {Object} options
             */
            VideoSocialSharingHandler = function(element, options) {
                if (!(this instanceof VideoSocialSharingHandler)) {
                    return new VideoSocialSharingHandler(element, options);
                }

                _.bindAll(this, 'clickHandler');

                this.container = element;

                if (this.container.find('.wrapper-downloads .wrapper-social-share')) {
                    this.initialize();
                }

                return false;
            };

            VideoSocialSharingHandler.prototype = {

                // Initializes the module.
                initialize: function() {
                    this.el = this.container.find('.wrapper-social-share');
                    this.el.on('click', '.btn-link', this.clickHandler);
                    this.baseVideoUrl = this.el.data('url');
                    this.course_id = this.container.data('courseId');
                    this.block_id = this.container.data('blockId');
                },

                // Fire an analytics event on share button click.
                clickHandler: function(event) {
                    var self = this;
                    var source = $(event.currentTarget).data('source');
                    self.sendAnalyticsEvent(source);
                },

                // Send an analytics event for share button tracking.
                sendAnalyticsEvent: function(source) {
                    window.analytics.track(
                        'edx.social.video.share_button.clicked',
                        {
                            source: source,
                            video_block_id: this.container.data('blockId'),
                            course_id: this.container.data('courseId'),
                        }
                    );
                }
            };

            return VideoSocialSharingHandler;
        });
}(RequireJS.define));
