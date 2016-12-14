var edx = edx || {},
    Language = (function() {
        'use strict';
        var preference_api_url,
            settings_language_selector,
            self = null;
        return {
            init: function() {
                preference_api_url = $('#preference-api-url').val();
                settings_language_selector = $('#settings-language-value');
                self = this;
                this.listenForLanguagePreferenceChange();
            },

            /**
             * Listener on changing language from selector.
             * Send an ajax request to save user language preferences.
             */
            listenForLanguagePreferenceChange: function() {
                settings_language_selector.change(function(event) {
                    var language = this.value;
                    event.preventDefault();
                    $.ajax({
                        type: 'PATCH',
                        data: JSON.stringify({'pref-lang': language}) ,
                        url: preference_api_url,
                        dataType: 'json',
                        contentType: "application/merge-patch+json",
                        beforeSend: function (xhr) {
                            xhr.setRequestHeader("X-CSRFToken", $('#csrf_token').val());
                        }
                    }).done(function () {
                        // User language preference has been set successfully
                        // Now submit the form in success callback.
                        $("#language-settings-form").submit();
                    }).fail(function() {
                        self.refresh();
                    });
                });
            },

            /**
             * refresh the page.
             */
            refresh: function () {
                // reloading the page so we can get the latest state of realsesd languages from model
                location.reload();
            }

        };
    })();
$(document).ready(function () {
    'use strict';
    Language.init();
});
