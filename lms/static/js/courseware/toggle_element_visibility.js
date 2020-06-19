(function(define) {
    'use strict';

    define(['jquery'],
        function($) {
            return function() {
                // define variables for code legibility
                var $toggleActionElements = $('.toggle-visibility-button');

                var updateToggleActionText = function(elementIsHidden, actionElement) {
                    var showText = actionElement.data('show'),
                        hideText = actionElement.data('hide'),
                        firstHiddenUpdate = $('.old-updates .toggle-visibility-button').first();

                    actionElement.attr('aria-expanded', elementIsHidden);

                    if (elementIsHidden) {
                        if (hideText) {
                            actionElement.html(actionElement.data('hide'));
                        } else {
                            actionElement.hide();
                            firstHiddenUpdate.focus();
                        }
                    } else {
                        if (showText) {
                            actionElement.html(actionElement.data('show'));
                        }
                    }
                };

                $.each($toggleActionElements, function(i, elem) {
                    var $toggleActionElement = $(elem),
                        toggleTargetElement = $toggleActionElement.siblings('.toggle-visibility-element'),
                        elementIsHidden = toggleTargetElement.is(':visible');

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
