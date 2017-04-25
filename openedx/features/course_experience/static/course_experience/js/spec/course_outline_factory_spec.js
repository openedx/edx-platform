define([
    'jquery',
    'logger',
    'edx-ui-toolkit/js/utils/constants',
    'course_experience/js/course_outline_factory'
],
    function($, Logger, constants, CourseOutlineFactory) {
        'use strict';

        describe('Course outline factory', function() {
            describe('keyboard listener', function() {
                var triggerKeyListener = function(current, destination, keyCode) {
                    current.focus();
                    spyOn(destination, 'focus');

                    $('.block-tree').trigger($.Event('keydown', {
                        keyCode: keyCode,
                        target: current
                    }));
                };

                beforeEach(function() {
                    loadFixtures('course_experience/fixtures/course-outline-fragment.html');
                    CourseOutlineFactory('.block-tree');
                });

                describe('when the down arrow is pressed', function() {
                    it('moves focus from a subsection to the next subsection in the outline', function() {
                        var current = $('a.focusable:contains("Homework - Labs and Demos")')[0],
                            destination = $('a.focusable:contains("Homework - Essays")')[0];

                        triggerKeyListener(current, destination, constants.keyCodes.down);

                        expect(destination.focus).toHaveBeenCalled();
                    });

                    it('moves focus to the section list if at a section boundary', function() {
                        var current = $('li.focusable:contains("Example Week 3: Be Social")')[0],
                            destination = $('ol.focusable:contains("Lesson 3 - Be Social")')[0];

                        triggerKeyListener(current, destination, constants.keyCodes.down);

                        expect(destination.focus).toHaveBeenCalled();
                    });

                    it('moves focus to the next section if on the last subsection', function() {
                        var current = $('a.focusable:contains("Homework - Essays")')[0],
                            destination = $('li.focusable:contains("Example Week 3: Be Social")')[0];

                        triggerKeyListener(current, destination, constants.keyCodes.down);

                        expect(destination.focus).toHaveBeenCalled();
                    });
                });

                describe('when the up arrow is pressed', function() {
                    it('moves focus from a subsection to the previous subsection in the outline', function() {
                        var current = $('a.focusable:contains("Homework - Essays")')[0],
                            destination = $('a.focusable:contains("Homework - Labs and Demos")')[0];

                        triggerKeyListener(current, destination, constants.keyCodes.up);

                        expect(destination.focus).toHaveBeenCalled();
                    });

                    it('moves focus to the section group if at the first subsection', function() {
                        var current = $('a.focusable:contains("Lesson 3 - Be Social")')[0],
                            destination = $('ol.focusable:contains("Lesson 3 - Be Social")')[0];

                        triggerKeyListener(current, destination, constants.keyCodes.up);

                        expect(destination.focus).toHaveBeenCalled();
                    });

                    it('moves focus last subsection of the previous section if at a section boundary', function() {
                        var current = $('li.focusable:contains("Example Week 3: Be Social")')[0],
                            destination = $('a.focusable:contains("Homework - Essays")')[0];

                        triggerKeyListener(current, destination, constants.keyCodes.up);

                        expect(destination.focus).toHaveBeenCalled();
                    });
                });
            });

            describe('eventing', function() {
                beforeEach(function() {
                    loadFixtures('course_experience/fixtures/course-outline-fragment.html');
                    CourseOutlineFactory('.block-tree');
                    spyOn(Logger, 'log');
                });

                it('sends an event when an outline section is clicked', function() {
                    $('a.focusable:contains("Homework - Labs and Demos")').click();

                    expect(Logger.log).toHaveBeenCalledWith('edx.ui.lms.link_clicked', {
                        target_url: window.location.origin +
                            '/courses/course-v1:edX+DemoX+Demo_Course/jump_to/block-v1:edX+DemoX+Demo_Course+type' +
                            '@sequential+block@graded_simulations',
                        current_url: window.location.toString()
                    });
                });
            });
        });
    }
);
