define(['backbone', 'jquery', 'underscore', 'js/common_helpers/ajax_helpers', 'js/common_helpers/template_helpers',
        'js/spec/views/fields_helpers', 'logger',
        'string_utils'],
    function (Backbone, $, _, AjaxHelpers, TemplateHelpers, FieldViewsSpecHelpers, Logger) {
        'use strict';

        var verifyAuthField = function (view, data, requests, event_user_id) {
            var selector = '.u-field-value > a', eventData;

            spyOn(view, 'redirect_to');

            FieldViewsSpecHelpers.expectTitleAndMessageToBe(view, data.title, data.helpMessage);
            expect(view.$(selector).text().trim()).toBe('Unlink');
            view.$(selector).click();

            if (event_user_id) {
                eventData = {
                    'setting': data.valueAttribute,
                    'old': 'connected',
                    'new': 'disconnected',
                    'user_id': event_user_id
                };
                expect(Logger.log).toHaveBeenCalledWith("edx.user.settings.change_initiated", eventData);
            }
            else {
                expect(Logger.log).not.toHaveBeenCalled();
            }

            FieldViewsSpecHelpers.expectMessageContains(view, 'Unlinking');
            AjaxHelpers.expectRequest(requests, 'POST', data.disconnectUrl);
            AjaxHelpers.respondWithNoContent(requests);

            expect(view.$(selector).text().trim()).toBe('Link');
            FieldViewsSpecHelpers.expectMessageContains(view, 'Successfully unlinked.');

            view.$(selector).click();

            if (event_user_id) {
                eventData = {
                    'setting': data.valueAttribute,
                    'old': 'disconnected',
                    'new': 'connected',
                    'user_id': event_user_id
                };
                expect(Logger.log).toHaveBeenCalledWith("edx.user.settings.change_initiated", eventData);
            }
            else {
                expect(Logger.log).not.toHaveBeenCalled();
            }

            FieldViewsSpecHelpers.expectMessageContains(view, 'Linking');
            expect(view.redirect_to).toHaveBeenCalledWith(data.connectUrl);
        };

        return {
            verifyAuthField: verifyAuthField
        };
    });
