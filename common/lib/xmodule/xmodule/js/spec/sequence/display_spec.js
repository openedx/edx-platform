/* globals Sequence */
(function() {
    'use strict';

    describe('Sequence', function() {
        var local = {},
            keydownHandler,
            keys = {
                ENTER: 13,
                LEFT: 37,
                RIGHT: 39
            },
            origin = 'https://www.example.com/',
            pathname = 'courses/course-v1:edX+DemoX+Demo_Course/courseware/unit_id/title/',
            unit,
            position,
            updateBrowserUrl;

        beforeEach(function() {
            loadFixtures('sequence.html');
            local.XBlock = window.XBlock = jasmine.createSpyObj('XBlock', ['initializeBlocks']);
            this.sequence = new Sequence($('.xblock-student_view-sequential'));

            spyOn(this.sequence, 'getUrlParts').and.callFake(function() {
                return [origin, pathname];
            });

            spyOn(this.sequence, 'determineBrowserUrl').and.callThrough();

            spyOn(this.sequence, 'previousNav').and.callThrough();

            spyOn(this.sequence, 'nextNav').and.callThrough();
        });

        afterEach(function() {
            delete local.XBlock;
        });

        keydownHandler = function(key) {
            var event = document.createEvent('Event');
            event.keyCode = key;
            event.initEvent('keydown', false, false);
            document.dispatchEvent(event);
        };

        updateBrowserUrl = function(sequence, position) {
            var urlParts = sequence.getUrlParts();
            var newUrl = sequence.determineBrowserUrl(urlParts[0], urlParts[1], position);
            return newUrl;
        };
        
        describe('Navbar', function() {
            it('appends the unit number in URL on page load', function() {
                unit = this.sequence.$('.nav-item[data-index=0]').focus();
                position = unit.data('element');
                expect(updateBrowserUrl(this.sequence, position)).toBe(origin + pathname + '1');
            });

            it('updates the unit number in URL when going to the previous unit', function() {
                unit = this.sequence.$('.nav-item[data-index=1]').focus();
                this.sequence.previousNav(unit, unit.data('index'));
                position = this.sequence.$('.nav-item.focused').data('element');
                expect(updateBrowserUrl(this.sequence, position)).toBe(origin + pathname + '1');
            });

            it('updates the unit number in URL when going to the next unit', function() {
                unit = this.sequence.$('.nav-item[data-index=1]').focus();
                this.sequence.nextNav(unit, unit.data('index'), this.sequence.$('.nav-item').length-1);
                position = this.sequence.$('.nav-item.focused').data('element');
                expect(updateBrowserUrl(this.sequence, position)).toBe(origin + pathname + '3');
            });

            it('updates the unit number in URL when jumping to the last unit in the previous section', function() {
                unit = this.sequence.$('.nav-item[data-index=0]').focus();
                this.sequence.previousNav(unit, unit.data('index'));
                position = this.sequence.$('.nav-item.focused').data('element');
                expect(updateBrowserUrl(this.sequence, position)).toBe(origin + pathname + '3');
            });

            it('updates the unit number in URL when jumping to the first unit in the next section', function() {
                unit = this.sequence.$('.nav-item[data-index=2]').focus();
                this.sequence.nextNav(unit, unit.data('index'), this.sequence.$('.nav-item').length-1);
                position = this.sequence.$('.nav-item.focused').data('element');
                expect(updateBrowserUrl(this.sequence, position)).toBe(origin + pathname + '1');
            });

            it('works with keyboard navigation LEFT and ENTER', function() {
                this.sequence.$('.nav-item[data-index=0]').focus();
                keydownHandler(keys.LEFT);
                keydownHandler(keys.ENTER);

                expect(this.sequence.$('.nav-item[data-index=1]')).toHaveAttr({
                    'aria-expanded': 'false',
                    'aria-selected': 'false',
                    tabindex: '-1'
                });
                expect(this.sequence.$('.nav-item[data-index=0]')).toHaveAttr({
                    'aria-expanded': 'true',
                    'aria-selected': 'true',
                    tabindex: '0'
                });
            });

            it('works with keyboard navigation RIGHT and ENTER', function() {
                this.sequence.$('.nav-item[data-index=0]').focus();
                keydownHandler(keys.RIGHT);
                keydownHandler(keys.ENTER);

                expect(this.sequence.$('.nav-item[data-index=0]')).toHaveAttr({
                    'aria-expanded': 'false',
                    'aria-selected': 'false',
                    tabindex: '-1'
                });
                expect(this.sequence.$('.nav-item[data-index=1]')).toHaveAttr({
                    'aria-expanded': 'true',
                    'aria-selected': 'true',
                    tabindex: '0'
                });
            });

            it('Completion Indicator missing', function() {
                this.sequence.$('.nav-item[data-index=0]').children('.check-circle').remove();
                spyOn($, 'postWithPrefix').and.callFake(function(url, data, callback) {
                    callback({
                        complete: true
                    });
                });
                this.sequence.update_completion(1);
                expect($.postWithPrefix).not.toHaveBeenCalled();
            });

            describe('Completion', function() {
                beforeEach(function() {
                    expect(
                        this.sequence.$('.nav-item[data-index=0]').children('.check-circle').first()
                        .hasClass('is-hidden')
                    ).toBe(true);
                    expect(
                        this.sequence.$('.nav-item[data-index=1]').children('.check-circle').first()
                        .hasClass('is-hidden')
                    ).toBe(true);
                });

                afterEach(function() {
                    expect($.postWithPrefix).toHaveBeenCalled();
                    expect(
                        this.sequence.$('.nav-item[data-index=1]').children('.check-circle').first()
                        .hasClass('is-hidden')
                    ).toBe(true);
                });

                it('API check returned true', function() {
                    spyOn($, 'postWithPrefix').and.callFake(function(url, data, callback) {
                        callback({
                            complete: true
                        });
                    });
                    this.sequence.update_completion(1);
                    expect(
                        this.sequence.$('.nav-item[data-index=0]').children('.check-circle').first()
                        .hasClass('is-hidden')
                    ).toBe(false);
                });

                it('API check returned false', function() {
                    spyOn($, 'postWithPrefix').and.callFake(function(url, data, callback) {
                        callback({
                            complete: false
                        });
                    });
                    this.sequence.update_completion(1);
                    expect(
                        this.sequence.$('.nav-item[data-index=0]').children('.check-circle').first()
                        .hasClass('is-hidden')
                    ).toBe(true);
                });
            });
        });
    });
}).call(this);
