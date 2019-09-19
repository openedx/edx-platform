define([
    'jquery', 'gettext', 'js/models/settings/advanced', 'js/views/settings/advanced'
], function($, gettext, AdvancedSettingsModel, AdvancedSettingsView) {
    'use strict';
    return function(advancedDict, advancedSettingsUrl, publisherEnabled) {
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

        // set the hidden property to true on relevant fields if publisher is enabled
        if (publisherEnabled && advancedModel.attributes) {
            Object.keys(advancedModel.attributes).forEach(function(am) {
                var field = advancedModel.attributes[am];
                field.hidden = field.hide_on_enabled_publisher;
            });
        }

        editor = new AdvancedSettingsView({
            el: $('.settings-advanced'),
            model: advancedModel
        });
        editor.render();

        $('#deprecated-settings').click(function() {
            var $wrapperDeprecatedSetting = $('.wrapper-deprecated-setting'),
                $deprecatedSettingsLabel = $('.deprecated-settings-label');

            if ($(this).is(':checked')) {
                $wrapperDeprecatedSetting.addClass('is-set');
                $deprecatedSettingsLabel.text(gettext('Hide Deprecated Settings'));
                editor.render_deprecated = true;
            } else {
                $wrapperDeprecatedSetting.removeClass('is-set');
                $deprecatedSettingsLabel.text(gettext('Show Deprecated Settings'));
                editor.render_deprecated = false;
            }

            editor.render();
        });
    };
});
