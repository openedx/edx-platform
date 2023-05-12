(function(define) {
    'use strict';

    define(['jquery', 'logger', 'moment'],
        function($, Logger, moment) {
            return function() {
                // define variables for code legibility
                // eslint-disable-next-line no-var
                var $toggleActionElements = $('.toggle-visibility-button');

                // eslint-disable-next-line no-var
                var updateToggleActionText = function(elementIsHidden, actionElement) {
                    /* eslint-disable-next-line camelcase, no-var */
                    var show_text = actionElement.data('show'),
                        // eslint-disable-next-line camelcase
                        hide_text = actionElement.data('hide'),
                        // eslint-disable-next-line camelcase
                        first_hidden_update = $('.old-updates .toggle-visibility-button').first();

                    actionElement.attr('aria-expanded', elementIsHidden);

                    if (elementIsHidden) {
                        // eslint-disable-next-line camelcase
                        if (hide_text) {
                            actionElement.html(actionElement.data('hide')); // xss-lint: disable=javascript-jquery-html
                        } else {
                            actionElement.hide();
                            // eslint-disable-next-line camelcase
                            first_hidden_update.focus();
                        }
                    } else {
                        // eslint-disable-next-line camelcase
                        if (show_text) {
                            actionElement.html(actionElement.data('show')); // xss-lint: disable=javascript-jquery-html
                        }
                    }
                };

                $.each($toggleActionElements, function(i, elem) {
                    // eslint-disable-next-line no-var
                    var $toggleActionElement = $(elem),
                        toggleTargetElement = $toggleActionElement.siblings('.toggle-visibility-element'),
                        elementIsHidden = toggleTargetElement.is(':visible'),
                        date = toggleTargetElement.siblings('.date').text();

                    updateToggleActionText(elementIsHidden, $toggleActionElement);

                    $toggleActionElement.on('click', function(event) {
                        event.preventDefault();
                        toggleTargetElement.toggleClass('hidden');
                        updateToggleActionText(!toggleTargetElement.hasClass('hidden'), $toggleActionElement);
                        Logger.log('edx.course.home.course_update.toggled', {
                            action: elementIsHidden ? 'hide' : 'show',
                            publish_date: moment(date, 'MMM DD, YYYY').format()
                        });
                    });
                });
            };
        });
// eslint-disable-next-line no-undef
}(define || RequireJS.define));
