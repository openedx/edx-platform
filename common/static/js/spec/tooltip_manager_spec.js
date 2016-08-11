describe('TooltipManager', function() {
    'use strict';
    var PAGE_X = 100, PAGE_Y = 100, WIDTH = 100, HEIGHT = 100, DELTA = 10,
        showTooltip;

    beforeEach(function() {
        setFixtures(sandbox({
            'id': 'test-id',
            'data-tooltip': 'some text here.'
        }));
        this.element = $('#test-id');

        this.tooltip = new TooltipManager(document.body);
        jasmine.clock().install();
        // Set default dimensions to make testing easer.
        $('.tooltip').height(HEIGHT).width(WIDTH);

        // Re-write default jasmine-jquery to consider opacity.
        jasmine.addMatchers({
            toBeVisible: function() {
                return {
                    compare: function(actual) {
                        return {
                            pass: actual.is(':visible') || parseFloat(actual.css('opacity'))
                        };
                    }
                };
            },

            toBeHidden: function() {
                return {
                    compare: function(actual) {
                        return {
                            pass: actual.is(':hidden') || !parseFloat(actual.css('opacity'))
                        };
                    }
                };
            }
        });
    });

    afterEach(function() {
        this.tooltip.destroy();
        jasmine.clock().uninstall();
    });

    showTooltip = function(element) {
        element.trigger($.Event('mouseover', {
            pageX: PAGE_X,
            pageY: PAGE_Y
        }));
        jasmine.clock().tick(500);
    };

    it('can destroy itself', function() {
        showTooltip(this.element);
        expect($('.tooltip')).toBeVisible();
        this.tooltip.destroy();
        expect($('.tooltip')).not.toExist();
        showTooltip(this.element);
        expect($('.tooltip')).not.toExist();
    });

    it('should be shown when mouse is over the element', function() {
        showTooltip(this.element);
        expect($('.tooltip')).toBeVisible();
        expect($('.tooltip').text()).toBe('some text here.');
    });

    it('should be hidden when mouse is out of the element', function() {
        showTooltip(this.element);
        expect($('.tooltip')).toBeVisible();
        this.element.trigger($.Event('mouseout'));
        jasmine.clock().tick(50);
        expect($('.tooltip')).toBeHidden();
    });

    it('should be hidden when user clicks on the element', function() {
        showTooltip(this.element);
        expect($('.tooltip')).toBeVisible();
        this.element.trigger($.Event('click'));
        jasmine.clock().tick(50);
        expect($('.tooltip')).toBeHidden();
    });

    it('can be configured to show when user clicks on the element', function() {
        this.element.attr('data-tooltip-show-on-click', true);
        this.element.trigger($.Event('click'));
        expect($('.tooltip')).toBeVisible();
    });

    it('can be be triggered manually', function() {
        this.tooltip.openTooltip(this.element);
        expect($('.tooltip')).toBeVisible();
    });

    it('should moves correctly', function() {
        showTooltip(this.element);
        expect($('.tooltip')).toBeVisible();
        // PAGE_X - 0.5 * WIDTH
        // 100 - 0.5 * 100 = 50
        expect(parseInt($('.tooltip').css('left'))).toBe(50);
        // PAGE_Y - (HEIGHT + 15)
        // 100 - (100 + 15) = -15
        expect(parseInt($('.tooltip').css('top'))).toBe(-15);
        this.element.trigger($.Event('mousemove', {
            pageX: PAGE_X + DELTA,
            pageY: PAGE_Y + DELTA
        }));
        // PAGE_X + DELTA - 0.5 * WIDTH
        // 100 + 10 - 0.5 * 100 = 60
        expect(parseInt($('.tooltip').css('left'))).toBe(60);
        // PAGE_Y + DELTA - (HEIGHT + 15)
        // 100 + 10 - (100 + 15) = -5
        expect(parseInt($('.tooltip').css('top'))).toBe(-5);
    });
});
