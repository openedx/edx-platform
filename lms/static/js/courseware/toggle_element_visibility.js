(function(define) {
    'use strict';

    define(['jquery'],
        function($) {
            return function() {
                // define variables for code legibility
                var $toggleActionElements = $('.toggle-visibility-button');

                var updateToggleActionText = function(elementIsHidden, actionElement) {
                    var show_text = actionElement.data('show'),
                        hide_text = actionElement.data('hide'),
                        first_hidden_update = $('.old-updates .toggle-visibility-button').first();

                    actionElement.attr('aria-expanded', elementIsHidden);

                    if (elementIsHidden) {
                        if (hide_text) {
                            actionElement.html(actionElement.data('hide'));
                        } else {
                            actionElement.hide();
                            first_hidden_update.focus();
                        }
                    } else {
                        if (show_text) {
                            actionElement.html(actionElement.data('show'));
                        }
                    }
                };

                $.each($toggleActionElements, function(i, elem) {
                    var $toggleActionElement = $(elem),
                        toggleTargetElement = $toggleActionElement.siblings('.toggle-visibility-element'),
                        elementIsHidden = toggleTargetElement.is(':visible'),
                        date = toggleTargetElement.siblings('.date').text();

                    updateToggleActionText(elementIsHidden, $toggleActionElement);

                    $toggleActionElement.on('click', function(event) {
                        event.preventDefault();
                        toggleTargetElement.toggleClass('hidden');
                        updateToggleActionText(!toggleTargetElement.hasClass('hidden'), $toggleActionElement);
                    });
                });
            };
        });
}(define || RequireJS.define));
