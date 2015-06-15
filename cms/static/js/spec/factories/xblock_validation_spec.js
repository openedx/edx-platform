define(['jquery', 'js/factories/xblock_validation', 'common/js/spec_helpers/template_helpers'],
    function($, XBlockValidationFactory, TemplateHelpers) {

        describe('XBlockValidationFactory', function() {
            var messageDiv;

            beforeEach(function () {
                TemplateHelpers.installTemplate('xblock-validation-messages');
                appendSetFixtures($('<div class="messages"></div>'));
                messageDiv = $('.messages');
            });

            it('Does not attach a view if messages is empty', function() {
                XBlockValidationFactory({"empty": true}, false, false, messageDiv);
                expect(messageDiv.children().length).toEqual(0);
            });

            it('Does attach a view if messages are not empty', function() {
                XBlockValidationFactory({"empty": false}, false, false, messageDiv);
                expect(messageDiv.children().length).toEqual(1);
            });

            it('Passes through the root property to the view.', function() {
                var noContainerContent = "no-container-content";

                var notConfiguredMessages = {
                    "empty": false,
                    "summary": {"text": "my summary", "type": "not-configured"},
                    "messages": [],
                    "xblock_id": "id"
                };
                // Root is false, will not add noContainerContent.
                XBlockValidationFactory(notConfiguredMessages, true, false, messageDiv);
                expect(messageDiv.find('.validation')).not.toHaveClass(noContainerContent);

                // Root is true, will add noContainerContent.
                XBlockValidationFactory(notConfiguredMessages, true, true, messageDiv);
                expect(messageDiv.find('.validation')).toHaveClass(noContainerContent);
            });

            describe('Controls display of detailed messages based on url and root property', function() {
                var messagesWithSummary, checkDetailedMessages;

                beforeEach(function () {
                    messagesWithSummary = {
                        "empty": false,
                        "summary": {"text": "my summary"},
                        "messages": [{"text": "one", "type": "warning"}, {"text": "two", "type": "error"}],
                        "xblock_id": "id"
                    };
                });

                checkDetailedMessages = function (expectedDetailedMessages) {
                    expect(messageDiv.children().length).toEqual(1);
                    expect(messageDiv.find('.xblock-message-item').length).toBe(expectedDetailedMessages);
                };

                it('Does not show details if xblock has an editing URL and it is not rendered as root', function() {
                    XBlockValidationFactory(messagesWithSummary, true, false, messageDiv);
                    checkDetailedMessages(0);
                });

                it('Shows details if xblock does not have its own editing URL, regardless of root value', function() {
                    XBlockValidationFactory(messagesWithSummary, false, false, messageDiv);
                    checkDetailedMessages(2);

                    XBlockValidationFactory(messagesWithSummary, false, true, messageDiv);
                    checkDetailedMessages(2);
                });

                it('Shows details if xblock has its own editing URL and is rendered as root', function() {
                    XBlockValidationFactory(messagesWithSummary, true, true, messageDiv);
                    checkDetailedMessages(2);
                });
            });
        });
    }
);
