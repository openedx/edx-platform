define(['jquery', 'js/utils/navigation'], function($) {
    'use strict';

    describe('Course Navigation Accordion', function() {
        var accordion, button, heading, chapterContent, chapterMenu;

        beforeEach(function() {
            loadFixtures('js/fixtures/accordion.html');

            accordion = $('.accordion');
            button = accordion.children('.button-chapter');
            heading = button.children('.group-heading');
            chapterContent = accordion.children('.chapter-content-container');
            chapterMenu = chapterContent.children('.chapter-menu');

            spyOn($.fn, 'focus').andCallThrough();
            edx.util.navigation.init();
        });

        describe('constructor', function() {

            describe('always', function() {

                it('ensures accordion is present', function() {
                    expect(accordion.length).toBe(1);
                });

                it('ensures aria attributes are present', function() {
                    expect(chapterContent).toHaveAttr({
                        'aria-expanded': 'true'
                    });
                });

                it('ensures only one active item', function() {
                    expect(chapterMenu.find('.active').length).toBe(1);
                });
            });

            describe('open section with mouse click', function() {

                it('ensures new section is opened and previous section is closed', function() {
                    button:eq(1).click();

                    expect(chapterContent:eq(0)).not.toHaveClass('is-open');
                    expect(chapterContent:eq(1)).toHaveClass('is-open');

                    expect(button:eq(0)).not.toHaveClass('is-open');
                    expect(button:eq(1)).toHaveClass('is-open');

                    expect(chapterContent:eq(1).focus).toHaveBeenCalled();
                });

                it('ensure proper aria and attrs', function() {
                    expect(chapterContent:eq(1)).toHaveAttr({
                        'aria-expanded': 'false'
                    });
                    expect(chapterContent:eq(0)).toHaveAttr({
                        'aria-expanded': 'true'
                    });
                });
            });

            describe('open section with spacebar', function() {

                function keyPressEvent(key) {
                    return $.Event('keydown', { keyCode: key });
                }

                it('ensures new section is opened and previous section is closed', function() {
                    button:eq(1).focus();
                    button.trigger(keyPressEvent(32)); // Spacebar

                    expect(chapterContent:eq(0)).not.toHaveClass('is-open');
                    expect(chapterContent:eq(1)).toHaveClass('is-open');

                    expect(button:eq(0)).not.toHaveClass('is-open');
                    expect(button:eq(1)).toHaveClass('is-open');

                    expect(chapterContent:eq(1).focus).toHaveBeenCalled();
                });

                it('ensure proper aria and attrs', function() {
                    expect(chapterContent:eq(1)).toHaveAttr({
                        'aria-expanded': 'false'
                    });
                    expect(chapterContent:eq(0)).toHaveAttr({
                        'aria-expanded': 'true'
                    });
                });
            });
        });
    });
});