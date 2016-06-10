describe('TooltipManager', function () {
    'use strict';
    var showTooltip;

    beforeAll(function() {
        window.globalTooltipManager.destroy();
    });

    beforeEach(function () {
        setFixtures(sandbox({
          'id': 'test-id',
          'data-tooltip': 'some text here.'
        }));
        this.element = $('#test-id');
        this.element.text('Hover me');

        this.manager = new window.TooltipManager({el: document.body});
        jasmine.clock().install();

        // Re-write default jasmine-jquery to consider opacity.
        jasmine.addMatchers({
            toBeVisible: function() {
              return {
                  compare: function (actual) {
                      return {
                          pass: actual.is(':visible') || parseFloat(actual.css('opacity'))
                      };
                  }
              };
            },

            toBeHidden: function () {
                return {
                    compare: function (actual) {
                        return {
                            pass: actual.is(':hidden') || !parseFloat(actual.css('opacity'))
                        };
                    }
                };
            }
        });
    });

    afterEach(function () {
        this.manager.destroy();
        jasmine.clock().uninstall();
    });

    showTooltip = function (element) {
        element.trigger('mouseenter');
    };

    it('can destroy itself', function () {
        showTooltip(this.element);
        expect($('.tooltip')).toBeVisible();
        this.manager.destroy();
        expect($('.tooltip')).not.toExist();
        showTooltip(this.element);
        expect($('.tooltip')).not.toExist();
    });

    it('should be shown when mouse is over the element', function () {
        showTooltip(this.element);
        expect($('.tooltip')).toBeVisible();
        expect($('.tooltip-content').text()).toBe('some text here.');
    });

    it('should be hidden when mouse is out of the element', function () {
        showTooltip(this.element);
        expect($('.tooltip')).toBeVisible();
        this.element.trigger('mouseleave');
        jasmine.clock().tick(500);
        expect($('.tooltip')).toBeHidden();
    });

    it('should stay visible when mouse is over the tooltip', function () {
        showTooltip(this.element);
        expect($('.tooltip')).toBeVisible();
        this.element.trigger('mouseleave');
        jasmine.clock().tick(100);
        this.manager.tooltip.$el.trigger('mouseenter');
        jasmine.clock().tick(500);
        expect($('.tooltip')).toBeVisible();
        this.manager.tooltip.$el.trigger('mouseleave');
        jasmine.clock().tick(500);
        expect($('.tooltip')).toBeHidden();
    });

    it('should be shown when the element gets focus', function () {
        this.element.trigger('focus');
        expect($('.tooltip')).toBeVisible();
    });

    it('should be hidden when user clicks on the element', function () {
        showTooltip(this.element);
        expect($('.tooltip')).toBeVisible();
        this.element.trigger('click');
        expect($('.tooltip')).toBeHidden();
    });

    it('can be configured to show when user clicks on the element', function () {
        this.element.attr('data-tooltip-show-on-click', true);
        this.element.trigger('click');
        expect($('.tooltip')).toBeVisible();
    });

    it('can be be triggered manually', function () {
        this.manager.openTooltip(this.element);
        expect($('.tooltip')).toBeVisible();
    });
});
