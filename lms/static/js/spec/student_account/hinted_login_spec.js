define([
    'jquery',
    'underscore',
    'common/js/spec_helpers/template_helpers',
    'common/js/spec_helpers/ajax_helpers',
    'js/student_account/views/HintedLoginView',
], function($, _, TemplateHelpers, AjaxHelpers, HintedLoginView) {
    'use strict';
    describe('edx.student.account.HintedLoginView', function() {

        var view = null,
            requests = null,
            PLATFORM_NAME = 'edX',
            THIRD_PARTY_AUTH = {
                currentProvider: null,
                providers: [
                    {
                        id: 'oa2-google-oauth2',
                        name: 'Google',
                        iconClass: 'fa-google-plus',
                        loginUrl: '/auth/login/google-oauth2/?auth_entry=account_login',
                        registerUrl: '/auth/login/google-oauth2/?auth_entry=account_register'
                    },
                    {
                        id: 'oa2-facebook',
                        name: 'Facebook',
                        iconClass: 'fa-facebook',
                        loginUrl: '/auth/login/facebook/?auth_entry=account_login',
                        registerUrl: '/auth/login/facebook/?auth_entry=account_register'
                    }
                ]
            },
            HINTED_PROVIDER = "oa2-google-oauth2";

        var createHintedLoginView = function(test) {
            // Initialize the login view
            view = new HintedLoginView({
                thirdPartyAuth: THIRD_PARTY_AUTH,
                hintedProvider: HINTED_PROVIDER,
                platformName: PLATFORM_NAME
            });

            // Mock the redirect call
            spyOn( view, 'redirect' ).andCallFake( function() {} );

            view.render();
        };

        beforeEach(function() {
            setFixtures('<div id="hinted-login-form"></div>');
            TemplateHelpers.installTemplate('templates/student_account/hinted_login');
        });

        it('displays a choice as two buttons', function() {
            createHintedLoginView(this);

            expect($('.proceed-button.button-oa2-google-oauth2')).toBeVisible();
            expect($('.form-toggle')).toBeVisible();
            expect($('.proceed-button.button-oa2-facebook')).not.toBeVisible();
        });

        it('redirects the user to the hinted provider if the user clicks the proceed button', function() {
            createHintedLoginView(this);

            // Click the "Yes, proceed" button
            $('.proceed-button').click();

            expect(view.redirect).toHaveBeenCalledWith( '/auth/login/google-oauth2/?auth_entry=account_login' );
        });
    });
});
