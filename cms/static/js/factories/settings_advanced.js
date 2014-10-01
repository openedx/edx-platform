define([
    'jquery', 'gettext', 'js/models/settings/advanced', 'js/views/settings/advanced'
], function($, gettext, AdvancedSettingsModel, AdvancedSettingsView) {
    'use strict';
    return function (advancedDict, advancedSettingsUrl) {
        var advancedModel, editor;

        $('form :input')
            .focus(function() {
                $('label[for="' + this.id + '"]').addClass('is-focused');
            })
            .blur(function() {
                $('label').removeClass('is-focused');
            });

        // proactively populate advanced b/c it has the filtered list and doesn't really follow the model pattern
        advancedModel = new AdvancedSettingsModel(advancedDict, {parse: true});
        advancedModel.url = advancedSettingsUrl;

        editor = new AdvancedSettingsView({
            el: $('.settings-advanced'),
            model: advancedModel
        });
        editor.render();

        $('#deprecated-settings').click(function() {
            var wrapperDeprecatedSetting = $('.wrapper-deprecated-setting'),
                deprecatedSettingsLabel = $('.deprecated-settings-label');

            if ($(this).is(':checked')) {
                wrapperDeprecatedSetting.addClass('is-set');
                deprecatedSettingsLabel.text(gettext('Hide Deprecated Settings'));
                editor.render_deprecated = true;
            }
            else {
                wrapperDeprecatedSetting.removeClass('is-set');
                deprecatedSettingsLabel.text(gettext('Show Deprecated Settings'));
                editor.render_deprecated = false;
            }

            editor.render();
        });
    };
});
