define(['backbone',
    'jquery',
    'underscore',
    'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers',
    'common/js/spec_helpers/template_helpers',
    'js/student_account/models/user_account_model',
    'js/views/fields',
    'js/spec/views/fields_helpers',
    'js/spec/student_account/account_settings_fields_helpers',
    'js/student_account/views/account_settings_fields',
    'js/student_account/models/user_account_model',
    'string_utils'],
function(Backbone, $, _, AjaxHelpers, TemplateHelpers, UserAccountModel, FieldViews, FieldViewsSpecHelpers,
    AccountSettingsFieldViewSpecHelpers, AccountSettingsFieldViews) {
    'use strict';

    describe('edx.AccountSettingsFieldViews', function() {
        var requests,
            timerCallback, // eslint-disable-line no-unused-vars
            data;

        beforeEach(function() {
            timerCallback = jasmine.createSpy('timerCallback');
            jasmine.clock().install();
        });

        afterEach(function() {
            jasmine.clock().uninstall();
        });

        it('sends request to reset password on clicking link in PasswordFieldView', function() {
            requests = AjaxHelpers.requests(this);

            var fieldData = FieldViewsSpecHelpers.createFieldData(AccountSettingsFieldViews.PasswordFieldView, {
                linkHref: '/password_reset',
                emailAttribute: 'email',
                valueAttribute: 'password'
            });

            var view = new AccountSettingsFieldViews.PasswordFieldView(fieldData).render();
            expect(view.$('.u-field-value > button').is(':disabled')).toBe(false);
            view.$('.u-field-value > button').click();
            expect(view.$('.u-field-value > button').is(':disabled')).toBe(true);
            AjaxHelpers.expectRequest(requests, 'POST', '/password_reset', 'email=legolas%40woodland.middlearth');
            AjaxHelpers.respondWithJson(requests, {success: 'true'});
            FieldViewsSpecHelpers.expectMessageContains(
                view,
                "We've sent a message to legolas@woodland.middlearth. " +
                    'Click the link in the message to reset your password.'
            );
        });

        it('update time zone dropdown after country dropdown changes', function() {
            var baseSelector = '.u-field-value > select';
            var groupsSelector = baseSelector + '> optgroup';
            var groupOptionsSelector = groupsSelector + '> option';

            var timeZoneData = FieldViewsSpecHelpers.createFieldData(AccountSettingsFieldViews.TimeZoneFieldView, {
                valueAttribute: 'time_zone',
                groupOptions: [{
                    groupTitle: gettext('All Time Zones'),
                    selectOptions: FieldViewsSpecHelpers.SELECT_OPTIONS,
                    nullValueOptionLabel: 'Default (Local Time Zone)'
                }],
                persistChanges: true,
                required: true
            });
            var countryData = FieldViewsSpecHelpers.createFieldData(AccountSettingsFieldViews.DropdownFieldView, {
                valueAttribute: 'country',
                options: [['KY', 'Cayman Islands'], ['CA', 'Canada'], ['GY', 'Guyana']],
                persistChanges: true
            });

            var countryChange = {country: 'GY'};
            var timeZoneChange = {time_zone: 'Pacific/Kosrae'};

            var timeZoneView = new AccountSettingsFieldViews.TimeZoneFieldView(timeZoneData).render();
            var countryView = new AccountSettingsFieldViews.DropdownFieldView(countryData).render();

            requests = AjaxHelpers.requests(this);

            timeZoneView.listenToCountryView(countryView);

            // expect time zone dropdown to have single subheader ('All Time Zones')
            expect(timeZoneView.$(groupsSelector).length).toBe(1);
            expect(timeZoneView.$(groupOptionsSelector).length).toBe(3);
            expect(timeZoneView.$(groupOptionsSelector)[0].value).toBe(FieldViewsSpecHelpers.SELECT_OPTIONS[0][0]);

            // change country
            countryView.$(baseSelector).val(countryChange[countryData.valueAttribute]).change();
            countryView.$(baseSelector).focusout();
            FieldViewsSpecHelpers.expectAjaxRequestWithData(requests, countryChange);
            AjaxHelpers.respondWithJson(requests, {success: 'true'});

            AjaxHelpers.expectRequest(
                requests,
                'GET',
                '/api/user/v1/preferences/time_zones/?country_code=GY'
            );
            AjaxHelpers.respondWithJson(requests, [
                {time_zone: 'America/Guyana', description: 'America/Guyana (ECT, UTC-0500)'},
                {time_zone: 'Pacific/Kosrae', description: 'Pacific/Kosrae (KOST, UTC+1100)'}
            ]);

            // expect time zone dropdown to have two subheaders (country/all time zone sub-headers) with new values
            expect(timeZoneView.$(groupsSelector).length).toBe(2);
            expect(timeZoneView.$(groupOptionsSelector).length).toBe(6);
            expect(timeZoneView.$(groupOptionsSelector)[0].value).toBe('America/Guyana');

            // select time zone option from option
            timeZoneView.$(baseSelector).val(timeZoneChange[timeZoneData.valueAttribute]).change();
            timeZoneView.$(baseSelector).focusout();
            FieldViewsSpecHelpers.expectAjaxRequestWithData(requests, timeZoneChange);
            AjaxHelpers.respondWithJson(requests, {success: 'true'});
            timeZoneView.render();

            // expect time zone dropdown to have three subheaders (currently selected/country/all time zones)
            expect(timeZoneView.$(groupsSelector).length).toBe(3);
            expect(timeZoneView.$(groupOptionsSelector).length).toBe(6);
            expect(timeZoneView.$(groupOptionsSelector)[0].value).toBe('Pacific/Kosrae');
        });

        it('sends request to /i18n/setlang/ after changing language in LanguagePreferenceFieldView', function() {
            requests = AjaxHelpers.requests(this);

            var selector = '.u-field-value > select';
            var fieldData = FieldViewsSpecHelpers.createFieldData(AccountSettingsFieldViews.DropdownFieldView, {
                valueAttribute: 'language',
                options: FieldViewsSpecHelpers.SELECT_OPTIONS,
                persistChanges: true
            });

            var view = new AccountSettingsFieldViews.LanguagePreferenceFieldView(fieldData).render();

            data = {language: FieldViewsSpecHelpers.SELECT_OPTIONS[2][0]};
            view.$(selector).val(data[fieldData.valueAttribute]).change();
            view.$(selector).focusout();
            FieldViewsSpecHelpers.expectAjaxRequestWithData(requests, data);
            AjaxHelpers.respondWithNoContent(requests);

            AjaxHelpers.expectRequest(
                requests,
                'POST',
                '/i18n/setlang/',
                $.param({
                    language: data[fieldData.valueAttribute],
                    next: window.location.href
                })
            );
            // Django will actually respond with a 302 redirect, but that would cause a page load during these
            // unittests.  204 should work fine for testing.
            AjaxHelpers.respondWithNoContent(requests);
            FieldViewsSpecHelpers.expectMessageContains(view, 'Your changes have been saved.');

            data = {language: FieldViewsSpecHelpers.SELECT_OPTIONS[1][0]};
            view.$(selector).val(data[fieldData.valueAttribute]).change();
            view.$(selector).focusout();
            FieldViewsSpecHelpers.expectAjaxRequestWithData(requests, data);
            AjaxHelpers.respondWithNoContent(requests);

            AjaxHelpers.expectRequest(
                requests,
                'POST',
                '/i18n/setlang/',
                $.param({
                    language: data[fieldData.valueAttribute],
                    next: window.location.href
                })
            );
            AjaxHelpers.respondWithError(requests, 500);
            FieldViewsSpecHelpers.expectMessageContains(
                view,
                'You must sign out and sign back in before your language changes take effect.'
            );
        });

        it('reads and saves the value correctly for LanguageProficienciesFieldView', function() {
            requests = AjaxHelpers.requests(this);

            var selector = '.u-field-value > select';
            var fieldData = FieldViewsSpecHelpers.createFieldData(AccountSettingsFieldViews.DropdownFieldView, {
                valueAttribute: 'language_proficiencies',
                options: FieldViewsSpecHelpers.SELECT_OPTIONS,
                persistChanges: true
            });
            fieldData.model.set({language_proficiencies: [{code: FieldViewsSpecHelpers.SELECT_OPTIONS[0][0]}]});

            var view = new AccountSettingsFieldViews.LanguageProficienciesFieldView(fieldData).render();

            expect(view.modelValue()).toBe(FieldViewsSpecHelpers.SELECT_OPTIONS[0][0]);

            data = {language_proficiencies: [{code: FieldViewsSpecHelpers.SELECT_OPTIONS[1][0]}]};
            view.$(selector).val(FieldViewsSpecHelpers.SELECT_OPTIONS[1][0]).change();
            view.$(selector).focusout();
            FieldViewsSpecHelpers.expectAjaxRequestWithData(requests, data);
            AjaxHelpers.respondWithNoContent(requests);
        });

        it('correctly links and unlinks from AuthFieldView', function() {
            requests = AjaxHelpers.requests(this);

            var fieldData = FieldViewsSpecHelpers.createFieldData(FieldViews.LinkFieldView, {
                title: 'Yet another social network',
                helpMessage: '',
                valueAttribute: 'auth-yet-another',
                connected: true,
                acceptsLogins: 'true',
                connectUrl: 'yetanother.com/auth/connect',
                disconnectUrl: 'yetanother.com/auth/disconnect'
            });
            var view = new AccountSettingsFieldViews.AuthFieldView(fieldData).render();

            AccountSettingsFieldViewSpecHelpers.verifyAuthField(view, fieldData, requests);
        });
    });
});
