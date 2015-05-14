define(['backbone', 'jquery', 'underscore', 'js/views/message'
       ],
    function (Backbone, $, _, MessageView) {
        'use strict';

        describe("MessageView", function () {

            beforeEach(function () {
                setFixtures('<div class="message-banner"></div>');
                TemplateHelpers.installTemplate("templates/fields/message_banner");
                TemplateHelpers.installTemplate("templates/views/message");
            });

            it('renders message correctly', function() {
                var messageSelector = '.message-banner';
                var messageView = new MessageView({
                    el: $(messageSelector),
                    templateId: '#message_banner-tpl'
                });

                messageView.showMessage('I am message view');
                // Verify error message
                expect($(messageSelector).text().trim()).toBe('I am message view');

                messageView.hideMessage();
                expect($(messageSelector).text().trim()).toBe('');
            });
        });
    });
