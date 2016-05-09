(function() {
    'use strict';

    var Tooltip = Backbone.View.extend({
        className: 'tooltip',

        template: _.template('<div class="tooltip-content"><%= content %></div><div class="tooltip-arrow">▾</div>'),

        events: {
            'mouseenter': 'show',
            'mouseleave': 'hide',
            'focusout': 'focusout'
        },

        initialize: function(content) {
            this.content = content;
            this.timer = null;
        },

        // Display this tooltip.
        show: function() {
            if (this.timer) {
                clearTimeout(this.timer);
            }
            this.timer = null;
            this.$el.show().css('opacity', 1);
        },

        // Hide this tooltip. Includes a delay before the tooltip starts fading
        // out, and a second delay to allow the tooltip to fade out. Once the
        // tooltip is hidden, it is removed from the DOM, and the `removed`
        // event is triggered. If `show` is called before the tooltip is
        // removed, it is redisplayed.
        hide: function() {
            if (this.timer) {
                clearTimeout(this.timer);
            }
            var remove = _.bind(this.remove, this);
            var hide = _.bind(function() {
                this.$el.css('opacity', 0);
                _.delay(remove, 250);
            }, this);
            this.timer = _.delay(hide, 250);
        },

        // Remove the tooltip from the DOM, triggering the `removed` event.
        remove: function() {
            if (this.timer) {
                clearTimeout(this.timer);
            }
            this.timer = null;
            Backbone.View.prototype.remove.call(this);
            this.trigger('removed');
        },

        // Triggered when an element inside the tooltip loses focus. Only hides
        // the tooltip if the element that gains focus afterwards is not also a
        // part of the tooltip.
        focusout: function() {
            var remove = _.bind(function() {
                if (!this.$(':focus').length) {
                    this.remove();
                }
            }, this);
            _.defer(remove);
        },

        render: function() {
            this.$el.html(this.template({content: this.content}));
            return this;
        }
    });


    // Manages tooltips within a container element. Tooltips are constrained to
    // fit within the container element, and only one tooltip can be displayed
    // at any given time.
    var TooltipManager = Backbone.View.extend({
        SELECTOR: '[data-tooltip]',

        // Listen for events from elements that include the `data-tooltip`
        // attribute.
        events: function() {
            var events = {
                'mouseenter': this.showTooltip,
                'focus': this.showTooltip,
                'mouseleave': this.hideTooltip,
                'click': this.click
            };
            var selector = this.SELECTOR;
            var selected = {};
            _.each(events, function(value, key) {
                selected[key + ' ' + selector] = value;
            });
            return selected;
        },

        initialize: function() {
            _.bindAll(this, 'reset');
            this.reset();
        },

        // Reset the tooltip manager's internal state. Call this when all
        // tooltips have been hidden.
        reset: function() {
            this.tooltip = null;
            this.tooltipFor = null;
        },

        // Event handler for displaying tooltips. Opens the tooltip for the
        // triggering element.
        showTooltip: function(event) {
            this.openTooltip(event.currentTarget);
        },

        // Hide the currently displayed tooltip. By default, waits for a short
        // time before hiding the tooltip in case the mouse or focus re-enters
        // the element or the tooltip. If `options.immediately` is true, the
        // tooltip will be removed immediately, without a delay.
        hideTooltip: function(options) {
            if (!this.tooltip) {
                return;
            }
            if (options && options.immediately) {
                this.tooltip.remove();
            } else {
                this.tooltip.hide();
            }
        },

        // Handles the click event for triggering elements. If the
        // `data-tooltip-show-on-click` attribute is present, the tooltip will
        // remain open when the element is clicked.
        click: function(event) {
            var element = event.currentTarget,
                showOnClick = !!$(element).data('tooltip-show-on-click');  // Default is false
            if (showOnClick) {
                this.openTooltip(element);
            } else {
                this.hideTooltip({immediately: true});
            }
        },

        // Open the tooltip for the given element
        openTooltip: function(element) {

            // If the tooltip for the given element is already displayed,
            // all we need to do is cancel any queued hide actions.
            if (this.tooltipFor === element) {
                this.tooltip.show();
                return;
            }

            // Determine the coordinates and content of the tooltip
            var $element = $(element),
                offset = $element.offset(),
                x = offset.left + $element.outerWidth() / 2,
                y = offset.top,
                tooltipText = $element.data('tooltip');

            // Hide the currently displayed tooltip, if any
            this.hideTooltip({immediately: true});

            // Create a new tooltip and register is as the currently displayed
            // tooltip
            this.tooltip = new Tooltip(tooltipText);
            this.tooltipFor = element;

            // Insert the tooltip immediately after the triggering element, so
            // that focusable elements inside the tooltip get focus in the
            // correct order.
            this.tooltip.$el.insertAfter(element);

            // Reset the tooltip manager's internal state when the tooltip is
            // removed
            this.listenToOnce(this.tooltip, 'removed', this.reset);

            // Position the tooltip
            this.displayAt(x, y);
        },

        // Display the tooltip at the given coordinates. `x` and `y` are
        // relative to the container element.
        displayAt: function(x, y) {
            var parent = this.tooltip.$el.offsetParent(),
                offset = parent.offset();

            // Move the tooltip all the way to the left first so the width is
            // calculated correctly
            this.tooltip.show();
            this.tooltip.$el.css({left: -offset.left});
            this.tooltip.render();

            // Position the tooltip
            var coords = this.getRelativeCoords(parent, this.tooltip.$el.outerWidth(), x, y);
            this.tooltip.$el.css(coords);

            // If the tooltip is offset to the right by the left edge of the
            // viewport, move the arrow so it stays over the element
            this.tooltip.$('.tooltip-arrow').css({left: x - offset.left - coords.left});
        },

        // Return the coordinates for a tooltip of the given width, converted
        // to be relative to the given offset parent.
        getRelativeCoords: function(parent, width, x, y) {
            var coords = this.getCoords(width, x, y),
                offset = parent.offset(),
                parentWidth = parent.outerWidth(),
                parentHeight = parent.outerHeight();
            coords.left -= offset.left;
            coords.right -= this.$el.outerWidth() - offset.left - parentWidth;
            coords.bottom -= this.$el.outerHeight() - offset.top - parentHeight;
            return coords;
        },

        // Return the coordinates for a tooltip of the given width, such that
        // the tooltip does not go outside of the container element.
        getCoords: function(width, x, y) {
            var containerWidth = this.$el.outerWidth(),
                containerHeight = this.$el.outerHeight();
            return {
                left: Math.min(Math.max(0, x - width / 2), containerWidth - width),
                right: Math.max(0, containerWidth - x - width / 2),
                bottom: containerHeight - y + 15
            };
        },

        destroy: function () {
            this.hideTooltip({immediately: true});
            this.undelegateEvents();
            this.stopListening();
        }
    });

    window.TooltipManager = TooltipManager;

    // Instatiate a tooltip manager for the document body
    $(document).ready(function() {
        window.globalTooltipManager = new TooltipManager({el: document.body});
    });
}());
