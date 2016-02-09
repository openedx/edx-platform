;(function (define) {
    'use strict';

    define(['jquery', 'logger', 'moment'],
        function ($, Logger, moment) {

            return function () {
                // define variables for code legibility
                var toggleActionElements = $('.toggle-visibility-button');

                var updateToggleActionText = function (elementIsHidden, actionElement) {
                    var show_text = actionElement.data('show');
                    var hide_text = actionElement.data('hide');

                    if (elementIsHidden) {
                        if (hide_text) {
                            actionElement.html(actionElement.data('hide'));
                        } else {
                            actionElement.hide();
                        }
                    } else {
                        if (show_text) {
                            actionElement.html(actionElement.data('show'));
                        }
                    }
                };

                $.each(toggleActionElements, function (i, elem) {
                    var toggleActionElement = $(elem),
                        toggleTargetElement = toggleActionElement.siblings('.toggle-visibility-element'),
                        elementIsHidden = toggleTargetElement.is(':visible'),
                        date = toggleTargetElement.siblings('.date').text();

                    updateToggleActionText(elementIsHidden, toggleActionElement);

                    toggleActionElement.on('click', function (event) {
                        event.preventDefault();
                        toggleTargetElement.toggleClass('hidden');
                        updateToggleActionText(!toggleTargetElement.hasClass('hidden'), toggleActionElement);
                        Logger.log('edx.course.home.course_update.toggled', {
                            action: elementIsHidden ? 'hide' : 'show',
                            publish_date: moment(date, 'MMM DD, YYYY').format()
                        });
                    });
                });
            };
        });
})(define || RequireJS.define);
