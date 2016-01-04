define(['jquery', 'js/courseware/toggle_element_visibility'],
    function ($, ToggleElementVisibility) {
        'use strict';

        describe('show/hide with mouse click', function () {

            beforeEach(function() {
                loadFixtures('js/fixtures/courseware/course_updates.html');
                /*jshint newcap: false */
                ToggleElementVisibility();
                /*jshint newcap: true */
            });

            it('ensures update will hide on hide button click', function () {
                var $shownUpdate = $('.toggle-visibility-element:not(.hidden)').first();
                $shownUpdate.siblings('.toggle-visibility-button').trigger('click');
                expect($shownUpdate).toHaveClass('hidden');
            });

            it('ensures update will show on show button click', function () {
                var $hiddenUpdate = $('.toggle-visibility-element.hidden').first();
                $hiddenUpdate.siblings('.toggle-visibility-button').trigger('click');
                expect($hiddenUpdate).not.toHaveClass('hidden');
            });

            it('ensures old updates will show on button click', function () {
                // on page load old updates will be hidden
                var $oldUpdates = $('.toggle-visibility-element.old-updates');
                expect($oldUpdates).toHaveClass('hidden');

                // on click on show earlier update button old updates will be shown
                $('.toggle-visibility-button.show-older-updates').trigger('click');
                expect($oldUpdates).not.toHaveClass('hidden');
            });
        });
    });
