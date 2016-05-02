define(['jquery', 'js/utils/navigation'], function($) {
    'use strict';

    describe('Course Navigation Accordion', function() {
        var accordion, chapterMenu;

        function keyPressEvent(key) {
            return $.Event('keydown', { which: key });
        }

        beforeEach(function() {
            loadFixtures('js/fixtures/accordion.html');

            accordion = $('.accordion');
            chapterMenu = accordion.children('.chapter-content-container').children('.chapter-menu');

            this.KEY = $.ui.keyCode;
            spyOn($.fn, 'focus').andCallThrough();
            edx.util.navigation.init();
        });

        describe('constructor', function() {

            describe('always', function() {

                it('ensures accordion is present', function() {
                    expect(accordion.length).toBe(1);
                });

                it('ensures aria attributes are present', function() {
                    expect(accordion.find('.button-chapter').first()).toHaveAttr('aria-expanded', 'true');
                    expect(accordion.find('.button-chapter').last()).toHaveAttr('aria-expanded', 'false');
                });

                it('ensures only one active item', function() {
                    expect($(chapterMenu).find('.active').length).toBe(1);
                });
            });

            describe('open section with mouse click', function() {

                it('ensures new section is opened and previous section is closed', function() {
                    accordion.find('.button-chapter').last().trigger('click');

                    expect(accordion.find('.chapter-content-container').first()).not.toHaveClass('is-open');
                    expect(accordion.find('.chapter-content-container').last()).toHaveClass('is-open');

                    expect(accordion.find('.button-chapter').first()).not.toHaveClass('is-open');
                    expect(accordion.find('.button-chapter').last()).toHaveClass('is-open');
                });

                it('ensure proper aria and attrs', function() {
                    accordion.find('.button-chapter').last().trigger('click');

                    expect(accordion.find('.button-chapter').first()).toHaveAttr('aria-expanded', 'false');
                    expect(accordion.find('.button-chapter').last()).toHaveAttr('aria-expanded', 'true');
                });
            });

            describe('open section with spacebar', function() {

                it('ensures new section is opened and previous section is closed', function() {
                    accordion.find('.button-chapter').last().focus().trigger(keyPressEvent(this.KEY.SPACE));

                    expect(accordion.find('.chapter-content-container').first()).not.toHaveClass('is-open');
                    expect(accordion.find('.chapter-content-container').last()).toHaveClass('is-open');

                    expect(accordion.find('.button-chapter').first()).not.toHaveClass('is-open');
                    expect(accordion.find('.button-chapter').last()).toHaveClass('is-open');
                });

                it('ensure proper aria and attrs', function() {
                    accordion.find('.button-chapter').last().focus().trigger(keyPressEvent(this.KEY.SPACE));

                    expect(accordion.find('.button-chapter').first()).toHaveAttr('aria-expanded', 'false');
                    expect(accordion.find('.button-chapter').last()).toHaveAttr('aria-expanded', 'true');
                });
            });
        });
    });
});