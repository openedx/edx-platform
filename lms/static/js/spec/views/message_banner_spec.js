define(['backbone', 'jquery', 'underscore', 'js/views/message'
       ],
    function (Backbone, $, _, MessageView) {
        'use strict';

        describe("MessageView", function () {

            beforeEach(function () {
                setFixtures('<div class="message-banner"></div><div class="message"></div>');
                TemplateHelpers.installTemplate("templates/fields/message_banner");
                TemplateHelpers.installTemplate("templates/message_view");
            });

            var createMessageView = function (messageContainer, templateId) {
                return new MessageView({
                    el: $(messageContainer),
                    templateId: templateId
                });
            };

            it('renders message correctly with template with no icon', function() {
                var messageSelector = '.message-banner';
                var messageView = createMessageView(messageSelector, '#message_banner-tpl');

                messageView.showMessage('I am message view');
                expect($(messageSelector).text().trim()).toBe('I am message view');

                messageView.hideMessage();
                expect($(messageSelector).text().trim()).toBe('');
            });

            it('renders message correctly with template with icon', function() {
                var messageSelector = '.message';
                var messageView = createMessageView(messageSelector, '#message-tpl');
                var icon = '<i class="fa fa-thumbs-up"></i>';

                messageView.showMessage('I am message view', icon);

                expect($(messageSelector).text().trim()).toBe('I am message view');
                expect($(messageSelector).html()).toContain(icon);

                messageView.hideMessage();
                expect($(messageSelector).text().trim()).toBe('');
            });
        });
    });
