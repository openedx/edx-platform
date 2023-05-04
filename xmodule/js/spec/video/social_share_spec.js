(function() {
    'use strict';
    describe('VideoSocialSharingHandler', function() {
        var state, spyOpen;

        beforeEach(function() {
            state = jasmine.initializePlayer('video_all.html');
            spyOpen = spyOn(window, 'open').and.returnValue(null);
            window.analytics = jasmine.createSpyObj('analytics', ['track'])
        });

        afterAll(() => delete window.analytics);

        describe('clicking social share opens the correct URL', function() {
            const testCases = [
                { 
                    source: 'twitter',
                    url: "https://twitter.com/intent/tweet?text=Here's%20a%20fun%20clip%20from%20a%20class%20I'm%20taking%20on%20%40edXonline.%0A%0A&url="
                },
                { source: 'facebook', url: "https://www.facebook.com/sharer/sharer.php?u=" },
                { source: 'linkedin', url: 'https://www.linkedin.com/sharing/share-offsite/?url=' },
            ];
            _.each(testCases, ({ source, url }) => {
                it(source, () => {
                    var siteShareButton = $(`.social-share-link[data-source="${source}"]`);
                    expect(siteShareButton.length).toEqual(1);
    
                    siteShareButton.trigger('click');
                    expect(spyOpen).toHaveBeenCalledWith(
                        url + `video-share-url%3Futm_source%3D${source}%26utm_medium%3Dsocial%26utm_campaign%3Dsocial-share-exp`,
                        'targetWindow',
                        'toolbar=no,location=0,status=no,menubar=no,scrollbars=yes,resizable=yes,width=600,height=400'
                    );
    
                    expect(window.analytics.track).toHaveBeenCalledWith(
                        'edx.social.video.share_button.clicked',
                            {
                                source: source,
                                video_block_id: 'block-v1:coursekey+type@video+block@000000000000000000',
                                course_id: 'course-v1:someOrg+thisCOurse+runAway',
                            }
                    );
                });
            });
        });
    });
}).call(this);