define(['backbone', 'jquery', 'underscore', 'js/views/message_banner'
       ],
    function (Backbone, $, _, MessageBannerView) {
        'use strict';

        describe("MessageBannerView", function () {

            beforeEach(function () {
                setFixtures('<div class="message-banner"></div>');
                TemplateHelpers.installTemplate("templates/fields/message_banner");
            });

            it('renders message correctly', function() {
                var messageSelector = '.message-banner';
                var messageView = new MessageBannerView({
                    el: $(messageSelector)
                });

                messageView.showMessage('I am message view');
                // Verify error message
                expect($(messageSelector).text().trim()).toBe('I am message view');

                messageView.hideMessage();
                expect($(messageSelector).text().trim()).toBe('');
            });
        });
    });
