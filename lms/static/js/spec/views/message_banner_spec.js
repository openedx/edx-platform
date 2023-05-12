// eslint-disable-next-line no-undef
define(['backbone', 'jquery', 'underscore',
    'common/js/spec_helpers/template_helpers', 'js/views/message_banner'
],
function(Backbone, $, _, TemplateHelpers, MessageBannerView) {
    'use strict';

    describe('MessageBannerView', function() {
        beforeEach(function() {
            setFixtures('<div class="message-banner"></div>');
            TemplateHelpers.installTemplate('templates/fields/message_banner');
        });

        it('renders message correctly', function() {
            // eslint-disable-next-line no-var
            var messageSelector = '.message-banner';
            // eslint-disable-next-line no-var
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
