define(['jquery', 'js/utils/navigation'], function($) {
    'use strict';

    describe('Course Navigation Accordion', function() {
        var accordion, button, heading, chapterContent, chapterMenu;

        beforeEach(function() {
            loadFixtures('js/fixtures/accordion.html');

            accordion = $('#accordion');
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
                    expect(button).toHaveAttr({
                        'aria-pressed': 'true'
                    });

                    expect(chapterContent).toHaveAttr({
                        'aria-expanded': 'true'
                    });
                });

                it('ensures only one active item', function() {
                    expect(chapterMenu.find('.active').length).toBe(1);
                });
            });

            describe('open section', function() {

                it('ensures new section is opened and previous section is closed', function() {
                    button.last().click();

                    expect(chapterContent.first()).toBeHidden();
                    expect(chapterContent.last()).not.toBeHidden();

                    expect(button.first()).not.toHaveClass('is-open');
                    expect(button.last()).toHaveClass('is-open');

                    expect(chapterContent.last().focus).toHaveBeenCalled();
                });

                it('ensure proper aria and attrs', function() {
                    expect(button.last()).toHaveAttr({
                        'aria-pressed': 'false'
                    });
                    expect(button.first()).toHaveAttr({
                        'aria-pressed': 'true'
                    });
                    expect(chapterContent.last()).toHaveAttr({
                        'aria-expanded': 'false'
                    });
                    expect(chapterContent.first()).toHaveAttr({
                        'aria-expanded': 'true'
                    })
                });
            });
        });
    });
});