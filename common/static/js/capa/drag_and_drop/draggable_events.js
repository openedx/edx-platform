(function (requirejs, require, define) {
define([], function () {
return {
    'attachMouseEventsTo': function (element) {
        var self;

        self = this;

        this[element].mousedown(function (event) {
            self.mouseDown(event);
        });
        this[element].mouseup(function (event) {
            self.mouseUp(event);
        });
        this[element].mousemove(function (event) {
            self.mouseMove(event);
        });
    },

    'mouseDown': function (event) {
        if (this.mousePressed === false) {
            // So that the browser does not perform a default drag.
            // If we don't do this, each drag operation will
            // potentially cause the highlghting of the dragged element.
            event.preventDefault();
            event.stopPropagation();

            if (this.numDraggablesOnMe > 0) {
                return;
            }

            // If this draggable is just being dragged out of the
            // container, we must perform some additional tasks.
            if (this.inContainer === true) {
                if ((this.isReusable === true) && (this.isOriginal === true)) {
                    this.makeDraggableCopy(function (draggableCopy) {
                        draggableCopy.mouseDown(event);
                    });

                    return;
                }

                if (this.isOriginal === true) {
                    this.containerEl.hide();
                    this.iconEl.detach();
                }

                if (this.iconImgEl !== null) {
                    this.iconImgEl.css({
                        'width': this.iconWidth,
                        'height': this.iconHeight
                    });
                }
                this.iconEl.css({
                    'background-color': this.iconElBGColor,
                    'padding-left': this.iconElPadding,
                    'padding-right': this.iconElPadding,
                    'border': this.iconElBorder,
                    'width': this.iconWidth,
                    'height': this.iconHeight,
                    'left': event.pageX - this.state.baseImageEl.offset().left - this.iconWidth * 0.5 - this.iconElLeftOffset,
                    'top': event.pageY - this.state.baseImageEl.offset().top - this.iconHeight * 0.5
                });
                this.iconEl.appendTo(this.state.baseImageEl.parent());

                if (this.labelEl !== null) {
                    if (this.isOriginal === true) {
                        this.labelEl.detach();
                    }
                    this.labelEl.css({
                        'background-color': this.state.config.labelBgColor,
                        'padding-left': 8,
                        'padding-right': 8,
                        'border': '1px solid black',
                        'left': event.pageX - this.state.baseImageEl.offset().left - this.labelWidth * 0.5 - 9, // Account for padding, border.
                        'top': event.pageY - this.state.baseImageEl.offset().top + this.iconHeight * 0.5 + 5
                    });
                    this.labelEl.appendTo(this.state.baseImageEl.parent());
                }

                this.inContainer = false;
                if (this.isOriginal === true) {
                    this.state.numDraggablesInSlider -= 1;
                }
                // SR: global "screen reader" object in accessibility_tools.js
                window.SR.readText(gettext('dragging out of slider'));
            } else {
                window.SR.readText(gettext('dragging'));
            }

            this.zIndex = 1000;
            this.iconEl.css('z-index', '1000');
            if (this.labelEl !== null) {
                this.labelEl.css('z-index', '1000');
            }
            this.iconEl.attr('aria-grabbed', 'true').focus();
            this.toggleTargets(true);
            this.mousePressed = true;
            this.state.currentMovingDraggable = this;
        }
    },

    'mouseUp': function () {
        if (this.mousePressed === true) {
            this.state.currentMovingDraggable = null;
            this.iconEl.attr('aria-grabbed', 'false');

            this.checkLandingElement();
            if (this.inContainer === true) {
                window.SR.readText(gettext('dropped in slider'));
            } else {
                window.SR.readText(gettext('dropped on target'));
            }
            this.toggleTargets(false);
        }
    },

    'mouseMove': function (event) {
        if (this.mousePressed === true) {
            // Because we have also attached a 'mousemove' event to the
            // 'document' (that will do the same thing), let's tell the
            // browser not to bubble up this event. The attached event
            // on the 'document' will only be triggered when the mouse
            // pointer leaves the draggable while it is in the middle
            // of a drag operation (user moves the mouse very quickly).
            event.stopPropagation();

            this.iconEl.css({
                'left': event.pageX - this.state.baseImageEl.offset().left - this.iconWidth * 0.5 - this.iconElLeftOffset,
                'top': event.pageY - this.state.baseImageEl.offset().top - this.iconHeight * 0.5
            });

            if (this.labelEl !== null) {
                this.labelEl.css({
                    'left': event.pageX - this.state.baseImageEl.offset().left - this.labelWidth * 0.5 - 9, // Acoount for padding, border.
                    'top': event.pageY - this.state.baseImageEl.offset().top + this.iconHeight * 0.5 + 5
                });
            }
        }
    }
}; // End-of: return {
}); // End-of: define([], function () {
}(RequireJS.requirejs, RequireJS.require, RequireJS.define)); // End-of: (function (requirejs, require, define) {
