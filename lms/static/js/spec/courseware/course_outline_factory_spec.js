define([
    'jquery',
    'edx-ui-toolkit/js/utils/constants',
    'js/courseware/course_outline_factory'
],
    function($, constants, CourseOutlineFactory) {
        'use strict';

        describe('Course outline factory', function() {
            describe('keyboard listener', function() {
                beforeEach(function() {
                    loadFixtures('js/fixtures/courseware/course_outline.html');
                    CourseOutlineFactory('.block-tree');
                });

                describe('when the down arrow is pressed', function() {
                    it('moves focus from a subsection to the next subsection in the outline', function() {
                        var destination = $('a.focusable:contains("Homework - Essays")')[0],
                            current = $('a.focusable:contains("Homework - Labs and Demos")');

                        current.focus();
                        spyOn(destination, 'focus');

                        $('.block-tree').trigger($.Event('keydown', {
                            keyCode: constants.keyCodes.down,
                            target: current[0]
                        }));
                        expect(destination.focus).toHaveBeenCalled();
                    });

                    it('moves focus to the first subsection if at a section boundary', function() {

                    });

                    it('moves focus to the next section if on the last subsection', function() {

                    });
                });

                describe('when the up arrow is pressed', function() {
                    it('moves focus from a subsection to the previous subsection in the outline', function() {
                        var destination = $('a.focusable:contains("Homework - Labs and Demos")')[0],
                            current = $('a.focusable:contains("Homework - Essays")');

                        current.focus();
                        spyOn(destination, 'focus');

                        $('.block-tree').trigger($.Event('keydown', {
                            keyCode: constants.keyCodes.up,
                            target: current[0]
                        }));
                        expect(destination.focus).toHaveBeenCalled();
                    });

                    it('moves focus to the section group if at the first subsection', function() {

                    });

                    it('moves focus last subsection of the previous section if at a section boundary', function() {

                    });
                });
            });
        });
    }
);
