(function() {
    'use strict';
    var TooltipManager = function (element) {
        this.element = $(element);
        // If tooltip container already exist, use it.
        this.tooltip = $('div.' + this.className.split(/\s+/).join('.'));
        // Otherwise, create new one.
        if (!this.tooltip.length) {
            this.tooltip = $('<div />', {
                'class': this.className
            }).appendTo(this.element);
        }

        this.hide();
        _.bindAll(this);
        this.bindEvents();
    };

    TooltipManager.prototype = {
        // Space separated list of class names for the tooltip container.
        className: 'tooltip',
        SELECTOR: '[data-tooltip]',

        bindEvents: function () {
            this.element.on({
                'mouseover.TooltipManager': this.showTooltip,
                'mousemove.TooltipManager': this.moveTooltip,
                'mouseout.TooltipManager': this.hideTooltip,
                'click.TooltipManager': this.hideTooltip
            }, this.SELECTOR);
        },

        getCoords: function (pageX, pageY) {
            return {
                'left': pageX - 0.5 * this.tooltip.outerWidth(),
                'top': pageY - (this.tooltip.outerHeight() + 15)
            };
        },

        show: function () {
            this.tooltip.show().css('opacity', 1);
        },

        hide: function () {
            this.tooltip.hide().css('opacity', 0);
        },

        showTooltip: function(event) {
            var tooltipText = $(event.currentTarget).attr('data-tooltip');
            this.tooltip
                .html(tooltipText)
                .css(this.getCoords(event.pageX, event.pageY));

            if (this.tooltipTimer) {
                clearTimeout(this.tooltipTimer);
            }
            this.tooltipTimer = setTimeout(this.show, 500);
        },

        moveTooltip: function(event) {
            this.tooltip.css(this.getCoords(event.pageX, event.pageY));
        },

        hideTooltip: function() {
            clearTimeout(this.tooltipTimer);
            // Wait for a 50ms before hiding the tooltip to avoid blinking when
            // the item contains nested elements.
            this.tooltipTimer = setTimeout(this.hide, 50);
        },

        destroy: function () {
            this.tooltip.remove();
            // Unbind all delegated event handlers in the ".TooltipManager"
            // namespace.
            this.element.off('.TooltipManager', this.SELECTOR);
        }
    };

    window.TooltipManager = TooltipManager;
    $(document).ready(function () {
        new TooltipManager(document.body);
    });
}());
