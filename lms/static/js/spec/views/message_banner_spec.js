define(['backbone', 'jquery', 'underscore', 'js/views/message', 'js/common_helpers/template_helpers'
       ],
    function (Backbone, $, _, MessageView, TemplateHelpers) {
        'use strict';

        describe("MessageView", function () {

            var messageEl = '.message-banner';

            beforeEach(function () {
                setFixtures('<div class="message-banner"></div>');
                TemplateHelpers.installTemplate("templates/fields/message_banner");
                TemplateHelpers.installTemplate("templates/message_view");
            });

            var createMessageView = function (messageContainer, templateId) {
                return new MessageView({
                    el: $(messageContainer),
                    templateId: templateId
                });
            };

            it('renders correctly with the /fields/message_banner template', function() {
                var messageView = createMessageView(messageSelector, '#message_banner-tpl');

                messageView.showMessage('I am message view');
                expect($(messageEl).text().trim()).toBe('I am message view');

                messageView.hideMessage();
                expect($(messageEl).text().trim()).toBe('');
            });

            it('renders correctly with the /message_view template', function() {
                var messageView = createMessageView(messageEl, '#message-tpl');
                var icon = '<i class="fa fa-thumbs-up"></i>';

                messageView.showMessage('I am message view', icon);

                expect($(messageEl).text().trim()).toBe('I am message view');
                expect($(messageEl).html()).toContain(icon);

                messageView.hideMessage();
                expect($(messageEl).text().trim()).toBe('');
            });
        });
    });
