(function(define) {
    'use strict';
    // VideoSocialSharingHandler module.
    define(
        'video/036_video_social_sharing.js', ['underscore', 'gettext'],
        function(_, gettext) {
            var VideoSocialSharingHandler, SocialSharingSite, SimpleSocialSharingSite, facebook, linkedin, twitter;
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
                    this.block_id = this.container.data('blockId')
                    this.socialSharingSites = this.getSocialSharingSites()
                },

                clickHandler: function(event) {
                    var self = this;
                    event.preventDefault();
                    var source = $(event.currentTarget).data('source')
                    var utmQuery = $.param({
                        utm_source: source,
                        utm_medium: 'social',
                        utm_campaign: 'social-share-exp',
                    });
                    var sharedVideoUrl = encodeURIComponent(self.baseVideoUrl + "?" + utmQuery);
                    var socialShareSite = self.socialSharingSites[source];
                    var socialMediaShareLinkUrl = socialShareSite.generateShareUrl(sharedVideoUrl);
                    window.open(
                        socialMediaShareLinkUrl,
                        'targetWindow',
                        'toolbar=no,location=0,status=no,menubar=no,scrollbars=yes,resizable=yes,width=600,height=400'
                    );
                    self.sendAnalyticsEvent(source);
                },

                getSocialSharingSites: function() {
                    var socialSharingSites = {},
                    socialSharingSitesList = [
                        twitter, facebook, linkedin
                    ];

                    _.each(socialSharingSitesList, function(socialSharingSite) {
                        socialSharingSites[socialSharingSite.name] = socialSharingSite;
                    }, this);

                    return socialSharingSites;
                },

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

            // Define the social sharing sites and how they generate
            // a link to their share page.
            SocialSharingSite = function(name, generateShareUrl) {
                // A social sharing site with a name and a function to generate a share URL
                this.name = name;
                this.generateShareUrl = generateShareUrl;
            };
            SimpleSocialSharingSite = function(name, baseShareUrl) {
                // A social sharing site with a url that is a static string with the url appended
                this.name = name;
                this.generateShareUrl = (url) => baseShareUrl + url;
            }
            twitter = new SocialSharingSite(
                'twitter',
                url => {
                    var tweetText = encodeURIComponent(gettext("Here's a fun clip from a class I'm taking on @edXonline.\n\n"));
                    return "https://twitter.com/intent/tweet?text=" + tweetText + "&url=" + url;
                }
            );
            facebook = new SimpleSocialSharingSite('facebook', 'https://www.facebook.com/sharer/sharer.php?u=');
            linkedin = new SimpleSocialSharingSite('linkedin', 'https://www.linkedin.com/sharing/share-offsite/?url=');

            return VideoSocialSharingHandler;
        });
}(RequireJS.define));
