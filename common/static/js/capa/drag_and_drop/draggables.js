// Wrapper for RequireJS. It will make the standard requirejs(), require(), and
// define() functions from Require JS available inside the anonymous function.
//
// See https://edx-wiki.atlassian.net/wiki/display/LMS/Integration+of+Require+JS+into+the+system
(function (requirejs, require, define) {

define(['logme', 'update_input'], function (logme, updateInput) {
    return {
        'init': init
    };

    function init(state) {
        (function (c1) {
            while (c1 < state.config.draggables.length) {
                processDraggable(state, state.config.draggables[c1]);
                c1 += 1
            }
        }(0));

        state.updateArrowOpacity();

        $(document).mousemove(function (event) {
            documentMouseMove(state, event);
        });
    }

    function documentMouseMove(state, event) {
        if (state.currentMovingDraggable !== null) {
            state.currentMovingDraggable.iconEl.css(
                'left',
                event.pageX -
                    state.baseImageEl.offset().left -
                    state.currentMovingDraggable.iconWidth * 0.5
                    - state.currentMovingDraggable.iconElLeftOffset
            );
            state.currentMovingDraggable.iconEl.css(
                'top',
                event.pageY -
                    state.baseImageEl.offset().top -
                    state.currentMovingDraggable.iconHeight * 0.5
            );

            if (state.currentMovingDraggable.labelEl !== null) {
                state.currentMovingDraggable.labelEl.css(
                    'left',
                    event.pageX -
                        state.baseImageEl.offset().left -
                        state.currentMovingDraggable.labelWidth * 0.5
                        - 9 // Account for padding, border.
                );
                state.currentMovingDraggable.labelEl.css(
                    'top',
                    event.pageY -
                        state.baseImageEl.offset().top +
                        state.currentMovingDraggable.iconHeight * 0.5 +
                        5
                );
            }
        }
    }

    function makeDraggableCopy(callbackFunc) {
        var draggableObj, obj;

        draggableObj = {
            'uniqueId': /* this.uniqueId */ this.state.getUniqueId(), // Is newly set.

            'originalConfigObj': this.originalConfigObj,
            'stateDraggablesIndex': /* this.stateDraggablesIndex */ null, // Will be set.

            'id': this.id,

            'isReusable': this.isReusable,
            'isOriginal': false,

            'x': this.x,
            'y': this.y,

            'zIndex': this.zIndex,

            // Not needed, since a copy will never return to a container element.
            'containerEl': null,

            'iconEl': /* this.iconEl */ null, // Will be created.
            'iconElBGColor': this.iconElBGColor,
            'iconElPadding': this.iconElPadding,
            'iconElBorder': this.iconElBorder,
            'iconElLeftOffset': this.iconElLeftOffset,
            'iconWidth': this.iconWidth,
            'iconHeight': this.iconHeight,
            'iconWidthSmall': this.iconWidthSmall,
            'iconHeightSmall': this.iconHeightSmall,

            'labelEl': /* this.labelEl */ null, // Will be created.
            'labelWidth': this.labelWidth,

            'hasLoaded': this.hasLoaded,
            'inContainer': this.inContainer,
            'mousePressed': this.mousePressed,
            'onTarget': this.onTarget,
            'onTargetIndex': this.onTargetIndex,

            'state': this.state,

            'mouseDown': this.mouseDown,
            'mouseUp': this.mouseUp,
            'mouseMove': this.mouseMove,
            'checkLandingElement': this.checkLandingElement,
            'checkIfOnTarget': this.checkIfOnTarget,
            'snapToTarget': this.snapToTarget,
            'correctZIndexes': this.correctZIndexes,
            'moveBackToSlider': this.moveBackToSlider,

            'moveDraggableToTarget': this.moveDraggableToTarget,
            'moveDraggableToXY': this.moveDraggableToXY,

            'makeDraggableCopy': this.makeDraggableCopy
        };

        obj = draggableObj.originalConfigObj;

        if (obj.icon.length > 0) {
            draggableObj.iconEl = $('<img />');
            draggableObj.iconEl.attr('src', obj.icon);
            draggableObj.iconEl.load(function () {
                draggableObj.iconEl.css('position', 'absolute');
                draggableObj.iconEl.css('width', draggableObj.iconWidthSmall);
                draggableObj.iconEl.css('height', draggableObj.iconHeightSmall);
                draggableObj.iconEl.css('left', 50 - draggableObj.iconWidthSmall * 0.5);

                if (obj.label.length > 0) {
                    draggableObj.iconEl.css('top', 5);
                } else {
                    draggableObj.iconEl.css('top', 50 - draggableObj.iconHeightSmall * 0.5);
                }

                if (obj.label.length > 0) {
                    draggableObj.labelEl = $(
                        '<div ' +
                            'style=" ' +
                                'position: absolute; ' +
                                'color: black; ' +
                                'font-size: 0.95em; ' +
                            '" ' +
                        '>' +
                            obj.label +
                        '</div>'
                    );

                    draggableObj.labelEl.css('left', 50 - draggableObj.labelWidth * 0.5);
                    draggableObj.labelEl.css('top', 5 + draggableObj.iconHeightSmall + 5);

                    draggableObj.labelEl.mousedown(function (event) {
                        draggableObj.mouseDown.call(draggableObj, event);
                    });
                    draggableObj.labelEl.mouseup(function (event) {
                        draggableObj.mouseUp.call(draggableObj, event);
                    });
                    draggableObj.labelEl.mousemove(function (event) {
                        draggableObj.mouseMove.call(draggableObj, event);
                    });
                }

                // Attach events to "iconEl".
                draggableObj.iconEl.mousedown(function (event) {
                    draggableObj.mouseDown.call(draggableObj, event);
                });
                draggableObj.iconEl.mouseup(function (event) {
                    draggableObj.mouseUp.call(draggableObj, event);
                });
                draggableObj.iconEl.mousemove(function (event) {
                    draggableObj.mouseMove.call(draggableObj, event);
                });

                draggableObj.stateDraggablesIndex = draggableObj.state.draggables.push(draggableObj);

                setTimeout(function () {
                    callbackFunc(draggableObj);
                }, 0);
            });

            return;
        } else {
            if (obj.label.length > 0) {
                draggableObj.iconEl = $(
                    '<div ' +
                        'style=" ' +
                            'position: absolute; ' +
                            'color: black; ' +
                            'font-size: 0.95em; ' +
                        '" ' +
                    '>' +
                        obj.label +
                    '</div>'
                );

                draggableObj.iconEl.css('left', 50 - draggableObj.iconWidthSmall * 0.5);
                draggableObj.iconEl.css('top', 50 - draggableObj.iconHeightSmall * 0.5);
            }
        }

        // Attach events to "iconEl".
        draggableObj.iconEl.mousedown(function (event) {
            draggableObj.mouseDown.call(draggableObj, event);
        });
        draggableObj.iconEl.mouseup(function (event) {
            draggableObj.mouseUp.call(draggableObj, event);
        });
        draggableObj.iconEl.mousemove(function (event) {
            draggableObj.mouseMove.call(draggableObj, event);
        });

        draggableObj.stateDraggablesIndex = draggableObj.state.draggables.push(draggableObj);

        setTimeout(function () {
            callbackFunc(draggableObj);
        }, 0);

        return;
    }

    function moveDraggableToXY(newPosition) {
        var self, offset;

        if (this.hasLoaded === false) {
            self = this;

            setTimeout(function () {
                self.moveDraggableToXY(newPosition);
            }, 50);

            return;
        }

        if ((this.isReusable === true) && (this.isOriginal === true)) {
            this.makeDraggableCopy(function (draggableCopy) {
                draggableCopy.moveDraggableToXY(newPosition);
            });

            return;
        }

        offset = 0;
        if (this.state.config.targetOutline === true) {
            offset = 1;
        }

        this.inContainer = false;

        if (this.isOriginal === true) {
            this.containerEl.hide();
            this.iconEl.detach();
        }
        this.iconEl.css('background-color', this.iconElBGColor);
        this.iconEl.css('padding-left', this.iconElPadding);
        this.iconEl.css('padding-right', this.iconElPadding);
        this.iconEl.css('border', this.iconElBorder);
        this.iconEl.css('width', this.iconWidth);
        this.iconEl.css('height', this.iconHeight);
        this.iconEl.css(
            'left',
            newPosition.x - this.iconWidth * 0.5 + offset - this.iconElLeftOffset
        );
        this.iconEl.css(
            'top',
            newPosition.y - this.iconHeight * 0.5 + offset
        );
        this.iconEl.appendTo(this.state.baseImageEl.parent());

        if (this.labelEl !== null) {
            if (this.isOriginal === true) {
                this.labelEl.detach();
            }
            this.labelEl.css('background-color', this.state.config.labelBgColor);
            this.labelEl.css('padding-left', 8);
            this.labelEl.css('padding-right', 8);
            this.labelEl.css('border', '1px solid black');
            this.labelEl.css(
                'left',
                newPosition.x - this.labelWidth * 0.5 + offset - 9 // Account for padding, border.
            );
            this.labelEl.css(
                'top',
                newPosition.y - this.iconHeight * 0.5 + this.iconHeight + 5 + offset
            );
            this.labelEl.appendTo(this.state.baseImageEl.parent());
        }

        this.x = newPosition.x;
        this.y = newPosition.y;

        this.zIndex = 1000;
        this.correctZIndexes();

        if (this.isOriginal === true) {
            this.state.numDraggablesInSlider -= 1;
            this.state.updateArrowOpacity();
        }
    }

    function moveDraggableToTarget(target) {
        var self, offset;

        if (this.hasLoaded === false) {
            self = this;

            setTimeout(function () {
                self.moveDraggableToTarget(target);
            }, 50);

            return;
        }

        if ((this.isReusable === true) && (this.isOriginal === true)) {
            this.makeDraggableCopy(function (draggableCopy) {
                draggableCopy.moveDraggableToTarget(target);
            });

            return;
        }

        offset = 0;
        if (this.state.config.targetOutline === true) {
            offset = 1;
        }

        this.inContainer = false;

        if (this.isOriginal === true) {
            this.containerEl.hide();
            this.iconEl.detach();
        }
        this.iconEl.css('background-color', this.iconElBGColor);
        this.iconEl.css('padding-left', this.iconElPadding);
        this.iconEl.css('padding-right', this.iconElPadding);
        this.iconEl.css('border', this.iconElBorder);
        this.iconEl.css('width', this.iconWidth);
        this.iconEl.css('height', this.iconHeight);
        this.iconEl.css(
            'left',
            target.offset.left + 0.5 * target.w - this.iconWidth * 0.5 + offset - this.iconElLeftOffset
        );
        this.iconEl.css(
            'top',
            target.offset.top + 0.5 * target.h - this.iconHeight * 0.5 + offset
        );
        this.iconEl.appendTo(this.state.baseImageEl.parent());

        if (this.labelEl !== null) {
            if (this.isOriginal === true) {
                this.labelEl.detach();
            }
            this.labelEl.css('background-color', this.state.config.labelBgColor);
            this.labelEl.css('padding-left', 8);
            this.labelEl.css('padding-right', 8);
            this.labelEl.css('border', '1px solid black');
            this.labelEl.css(
                'left',
                target.offset.left + 0.5 * target.w - this.labelWidth * 0.5 + offset - 9 // Account for padding, border.
            );
            this.labelEl.css(
                'top',
                target.offset.top + 0.5 * target.h + this.iconHeight * 0.5 + 5 + offset
            );
            this.labelEl.appendTo(this.state.baseImageEl.parent());
        }

        target.addDraggable(this);

        this.zIndex = 1000;
        this.correctZIndexes();

        if (this.isOriginal === true) {
            this.state.numDraggablesInSlider -= 1;
            this.state.updateArrowOpacity();
        }

    }

    function processDraggable(state, obj) {
        var draggableObj;

        draggableObj = {
            'uniqueId': state.getUniqueId(),

            'originalConfigObj': obj,
            'stateDraggablesIndex': null,

            'id': obj.id,

            'isReusable': obj.can_reuse,
            'isOriginal': true,

            'x': -1,
            'y': -1,

            'zIndex': 1,

            'containerEl': null,

            'iconEl': null,
            'iconElBGColor': null,
            'iconElPadding': null,
            'iconElBorder': null,
            'iconElLeftOffset': null,
            'iconWidth': null,
            'iconHeight': null,
            'iconWidthSmall': null,
            'iconHeightSmall': null,

            'labelEl': null,
            'labelWidth': null,

            'hasLoaded': false,
            'inContainer': true,
            'mousePressed': false,
            'onTarget': null,
            'onTargetIndex': null,

            'state': state,

            'mouseDown': mouseDown,
            'mouseUp': mouseUp,
            'mouseMove': mouseMove,
            'checkLandingElement': checkLandingElement,
            'checkIfOnTarget': checkIfOnTarget,
            'snapToTarget': snapToTarget,
            'correctZIndexes': correctZIndexes,
            'moveBackToSlider': moveBackToSlider,

            'moveDraggableToTarget': moveDraggableToTarget,
            'moveDraggableToXY': moveDraggableToXY,

            'makeDraggableCopy': makeDraggableCopy
        };

        draggableObj.containerEl = $(
            '<div ' +
                'style=" ' +
                    'width: 100px; ' +
                    'height: 100px; ' +
                    'display: inline; ' +
                    'float: left; ' +
                    'overflow: hidden; ' +
                    'border-left: 1px solid #CCC; ' +
                    'border-right: 1px solid #CCC; ' +
                    'text-align: center; ' +
                    'position: relative; ' +
                '" ' +
                '></div>'
        );

        draggableObj.containerEl.appendTo(state.sliderEl);

        if (obj.icon.length > 0) {
            draggableObj.iconElBGColor = 'transparent';
            draggableObj.iconElPadding = 0;
            draggableObj.iconElBorder = 'none';
            draggableObj.iconElLeftOffset = 0;

            draggableObj.iconEl = $('<img />');
            draggableObj.iconEl.attr('src', obj.icon);
            draggableObj.iconEl.load(function () {
                draggableObj.iconWidth = this.width;
                draggableObj.iconHeight = this.height;

                if (draggableObj.iconWidth >= draggableObj.iconHeight) {
                    draggableObj.iconWidthSmall = 60;
                    draggableObj.iconHeightSmall = draggableObj.iconWidthSmall * (draggableObj.iconHeight / draggableObj.iconWidth);
                } else {
                    draggableObj.iconHeightSmall = 60;
                    draggableObj.iconWidthSmall = draggableObj.iconHeightSmall * (draggableObj.iconWidth / draggableObj.iconHeight);
                }

                draggableObj.iconEl.css('position', 'absolute');
                draggableObj.iconEl.css('width', draggableObj.iconWidthSmall);
                draggableObj.iconEl.css('height', draggableObj.iconHeightSmall);
                draggableObj.iconEl.css('left', 50 - draggableObj.iconWidthSmall * 0.5);

                if (obj.label.length > 0) {
                    draggableObj.iconEl.css('top', 5);
                } else {
                    draggableObj.iconEl.css('top', 50 - draggableObj.iconHeightSmall * 0.5);
                }

                draggableObj.iconEl.appendTo(draggableObj.containerEl);

                if (obj.label.length > 0) {
                    draggableObj.labelEl = $(
                        '<div ' +
                            'style=" ' +
                                'position: absolute; ' +
                                'color: black; ' +
                                'font-size: 0.95em; ' +
                            '" ' +
                        '>' +
                            obj.label +
                        '</div>'
                    );

                    draggableObj.labelEl.appendTo(draggableObj.containerEl);
                    draggableObj.labelWidth = draggableObj.labelEl.width();
                    draggableObj.labelEl.css('left', 50 - draggableObj.labelWidth * 0.5);
                    draggableObj.labelEl.css('top', 5 + draggableObj.iconHeightSmall + 5);

                    draggableObj.labelEl.mousedown(function (event) {
                        draggableObj.mouseDown.call(draggableObj, event);
                    });
                    draggableObj.labelEl.mouseup(function (event) {
                        draggableObj.mouseUp.call(draggableObj, event);
                    });
                    draggableObj.labelEl.mousemove(function (event) {
                        draggableObj.mouseMove.call(draggableObj, event);
                    });
                }

                draggableObj.hasLoaded = true;
            });
        } else {
            // To make life easier, if there is no icon, but there is a
            // label, we will create a label and store it as if it was an
            // icon. All the existing code will work, and the user will
            // see a label instead of an icon.
            if (obj.label.length > 0) {
                draggableObj.iconElBGColor = state.config.labelBgColor;
                draggableObj.iconElPadding = 8;
                draggableObj.iconElBorder = '1px solid black';
                draggableObj.iconElLeftOffset = 9;

                draggableObj.iconEl = $(
                    '<div ' +
                        'style=" ' +
                            'position: absolute; ' +
                            'color: black; ' +
                            'font-size: 0.95em; ' +
                        '" ' +
                    '>' +
                        obj.label +
                    '</div>'
                );

                draggableObj.iconEl.appendTo(draggableObj.containerEl);

                draggableObj.iconWidth = draggableObj.iconEl.width();
                draggableObj.iconHeight = draggableObj.iconEl.height();
                draggableObj.iconWidthSmall = draggableObj.iconWidth;
                draggableObj.iconHeightSmall = draggableObj.iconHeight;

                draggableObj.iconEl.css('left', 50 - draggableObj.iconWidthSmall * 0.5);
                draggableObj.iconEl.css('top', 50 - draggableObj.iconHeightSmall * 0.5);

                draggableObj.hasLoaded = true;
            } else {
                // If no icon and no label, don't create a draggable.
                return;
            }
        }

        // Attach events to "iconEl".
        draggableObj.iconEl.mousedown(function (event) {
            draggableObj.mouseDown.call(draggableObj, event);
        });
        draggableObj.iconEl.mouseup(function (event) {
            draggableObj.mouseUp.call(draggableObj, event);
        });
        draggableObj.iconEl.mousemove(function (event) {
            draggableObj.mouseMove.call(draggableObj, event);
        });

        // Attach events to "containerEl".
        draggableObj.containerEl.mousedown(function (event) {
            draggableObj.mouseDown.call(draggableObj, event);
        });
        draggableObj.containerEl.mouseup(function (event) {
            draggableObj.mouseUp.call(draggableObj, event);
        });
        draggableObj.containerEl.mousemove(function (event) {
            draggableObj.mouseMove.call(draggableObj, event);
        });

        state.numDraggablesInSlider += 1;
        draggableObj.stateDraggablesIndex = state.draggables.push(draggableObj) - 1;
    }

    function mouseDown(event) {
        if (this.mousePressed === false) {
            // So that the browser does not perform a default drag.
            // If we don't do this, each drag operation will
            // potentially cause the highlghting of the dragged element.
            event.preventDefault();
            event.stopPropagation();

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
                this.iconEl.css('background-color', this.iconElBGColor);
                this.iconEl.css('padding-left', this.iconElPadding);
                this.iconEl.css('padding-right', this.iconElPadding);
                this.iconEl.css('border', this.iconElBorder);
                this.iconEl.css('width', this.iconWidth);
                this.iconEl.css('height', this.iconHeight);
                this.iconEl.css(
                    'left',
                    event.pageX - this.state.baseImageEl.offset().left - this.iconWidth * 0.5 - this.iconElLeftOffset
                );
                this.iconEl.css(
                    'top',
                    event.pageY - this.state.baseImageEl.offset().top - this.iconHeight * 0.5
                );
                this.iconEl.appendTo(this.state.baseImageEl.parent());

                if (this.labelEl !== null) {
                    if (this.isOriginal === true) {
                        this.labelEl.detach();
                    }
                    this.labelEl.css('background-color', this.state.config.labelBgColor);
                    this.labelEl.css('padding-left', 8);
                    this.labelEl.css('padding-right', 8);
                    this.labelEl.css('border', '1px solid black');
                    this.labelEl.css(
                        'left',
                        event.pageX - this.state.baseImageEl.offset().left - this.labelWidth * 0.5 - 9 // Account for padding, border.
                    );
                    this.labelEl.css(
                        'top',
                        event.pageY - this.state.baseImageEl.offset().top + this.iconHeight * 0.5 + 5
                    );
                    this.labelEl.appendTo(this.state.baseImageEl.parent());
                }

                this.inContainer = false;
                if (this.isOriginal === true) {
                    this.state.numDraggablesInSlider -= 1;
                }
            }

            this.zIndex = 1000;
            this.iconEl.css('z-index', '1000');
            if (this.labelEl !== null) {
                this.labelEl.css('z-index', '1000');
            }

            this.mousePressed = true;
            this.state.currentMovingDraggable = this;
        }
    }

    function mouseUp() {
        if (this.mousePressed === true) {
            this.state.currentMovingDraggable = null;

            this.checkLandingElement();
        }
    }

    function mouseMove(event) {
        if (this.mousePressed === true) {
            // Because we have also attached a 'mousemove' event to the
            // 'document' (that will do the same thing), let's tell the
            // browser not to bubble up this event. The attached event
            // on the 'document' will only be triggered when the mouse
            // pointer leaves the draggable while it is in the middle
            // of a drag operation (user moves the mouse very quickly).
            event.stopPropagation();

            this.iconEl.css(
                'left',
                event.pageX - this.state.baseImageEl.offset().left - this.iconWidth * 0.5 - this.iconElLeftOffset
            );
            this.iconEl.css(
                'top',
                event.pageY - this.state.baseImageEl.offset().top - this.iconHeight * 0.5
            );

            if (this.labelEl !== null) {
                this.labelEl.css(
                    'left',
                    event.pageX - this.state.baseImageEl.offset().left - this.labelWidth * 0.5 - 9 // Acoount for padding, border.
                );
                this.labelEl.css(
                    'top',
                    event.pageY - this.state.baseImageEl.offset().top + this.iconHeight * 0.5 + 5
                );
            }
        }
    }

    // At this point the mouse was realeased, and we need to check
    // where the draggable eneded up. Based on several things, we
    // will either move the draggable back to the slider, or update
    // the input with the user's answer (X-Y position of the draggable,
    // or the ID of the target where it landed.
    function checkLandingElement() {
        var positionIE;

        this.mousePressed = false;
        positionIE = this.iconEl.position();

        if (this.state.config.individualTargets === true) {
            if (this.checkIfOnTarget(positionIE) === true) {
                this.correctZIndexes();
            } else {
                if (this.onTarget !== null) {
                    this.onTarget.removeDraggable(this);
                }

                this.moveBackToSlider();

                if (this.isOriginal === true) {
                    this.state.numDraggablesInSlider += 1;
                }
            }
        } else {
            if (
                (positionIE.left < 0) ||
                (positionIE.left + this.iconWidth > this.state.baseImageEl.width()) ||
                (positionIE.top < 0) ||
                (positionIE.top + this.iconHeight > this.state.baseImageEl.height())
            ) {
                this.moveBackToSlider();

                this.x = -1;
                this.y = -1;

                if (this.isOriginal === true) {
                    this.state.numDraggablesInSlider += 1;
                }
            } else {
                this.correctZIndexes();

                this.x = positionIE.left + this.iconWidth * 0.5;
                this.y = positionIE.top + this.iconHeight * 0.5;
            }
        }

        if (this.isOriginal === true) {
            this.state.updateArrowOpacity();
        }
        updateInput.update(this.state);
    }

    // Determine if a draggable, after it was relased, ends up on a
    // target. We do this by iterating over all of the targets, and
    // for each one we check whether the draggable's center is
    // within the target's dimensions.
    //
    // positionIE is the object as returned by
    //
    //     this.iconEl.position()
    function checkIfOnTarget(positionIE) {
        var c1, target;

        for (c1 = 0; c1 < this.state.targets.length; c1 += 1) {
            target = this.state.targets[c1];

            // If only one draggable per target is allowed, and
            // the current target already has a draggable on it
            // (with an ID different from the one we are checking
            // against), then go to next target.
            if (
                (this.state.config.onePerTarget === true) &&
                (target.draggableList.length === 1) &&
                (target.draggableList[0].uniqueId !== this.uniqueId)
            ) {
                continue;
            }

            // Check if the draggable's center coordinate is within
            // the target's dimensions. If not, go to next target.
            if (positionIE.top + this.iconHeight * 0.5 < target.offset.top) {
                continue;
            }
            if (positionIE.top + this.iconHeight * 0.5 > target.offset.top + target.h) {
                continue;
            }
            if (positionIE.left + this.iconWidth * 0.5 < target.offset.left) {
                continue;
            }
            if (positionIE.left + this.iconWidth * 0.5 > target.offset.left + target.w) {
                continue;
            }

            // If the draggable was moved from one target to
            // another, then we need to remove it from the
            // previous target's draggables list, and add it to the
            // new target's draggables list.
            if ((this.onTarget !== null) && (this.onTarget.id !== target.id)) {
                this.onTarget.removeDraggable(this);
                target.addDraggable(this);
            }
            // If the draggable was moved from the slider to a
            // target, remember the target, and add ID to the
            // target's draggables list.
            else if (this.onTarget === null) {
                target.addDraggable(this);
            }

            // Reposition the draggable so that it's center
            // coincides with the center of the target.
            this.snapToTarget(target);

            // Target was found.
            return true;
        }

        // Target was not found.
        return false;
    }

    function snapToTarget(target) {
        var offset;

        offset = 0;
        if (this.state.config.targetOutline === true) {
            offset = 1;
        }

        this.iconEl.css(
            'left',
            target.offset.left + 0.5 * target.w - this.iconWidth * 0.5 + offset - this.iconElLeftOffset
        );
        this.iconEl.css(
            'top',
            target.offset.top + 0.5 * target.h - this.iconHeight * 0.5 + offset
        );

        if (this.labelEl !== null) {
            this.labelEl.css(
                'left',
                target.offset.left + 0.5 * target.w - this.labelWidth * 0.5 + offset - 9 // Acoount for padding, border.
            );
            this.labelEl.css(
                'top',
                target.offset.top + 0.5 * target.h + this.iconHeight * 0.5 + 5 + offset
            );
        }
    }

    // Go through all of the draggables subtract 1 from the z-index
    // of all whose z-index is higher than the old z-index of the
    // current element. After, set the z-index of the current
    // element to 1 + N (where N is the number of draggables - i.e.
    // the highest z-index possible).
    //
    // This will make sure that after releasing a draggable, it
    // will be on top of all of the other draggables. Also, the
    // ordering of the visibility (z-index) of the other draggables
    // will not change.
    function correctZIndexes() {
        var c1, highestZIndex;

        highestZIndex = -10000;

        if (this.state.config.individualTargets === true) {
            if (this.onTarget.draggableList.length > 0) {
                for (c1 = 0; c1 < this.onTarget.draggableList.length; c1 += 1) {
                    if (
                        (this.onTarget.draggableList[c1].zIndex > highestZIndex) &&
                        (this.onTarget.draggableList[c1].zIndex !== 1000)
                    ) {
                        highestZIndex = this.onTarget.draggableList[c1].zIndex;
                    }
                }
            } else {
                highestZIndex = 0;
            }
        } else {
            for (c1 = 0; c1 < this.state.draggables.length; c1++) {
                if (this.inContainer === false) {
                    if (
                        (this.state.draggables[c1].zIndex > highestZIndex) &&
                        (this.state.draggables[c1].zIndex !== 1000)
                    ) {
                        highestZIndex = this.state.draggables[c1].zIndex;
                    }
                }
            }
        }

        if (highestZIndex === -10000) {
            highestZIndex = 0;
        }

        this.zIndex = highestZIndex + 1;

        this.iconEl.css('z-index', this.zIndex);
        if (this.labelEl !== null) {
            this.labelEl.css('z-index', this.zIndex);
        }
    }

    // If a draggable was released in a wrong positione, we will
    // move it back to the slider, placing it in the same position
    // that it was dragged out of.
    function moveBackToSlider() {
        var c1;

        if (this.isOriginal === false) {
            this.iconEl.empty();
            this.iconEl.remove();
            if (this.labelEl !== null) {
                this.labelEl.empty();
                this.labelEl.remove();
            }
            this.state.draggables.splice(this.stateDraggablesIndex, 1);

            c1 = 0;
            while (c1 < this.state.draggables) {
                if (this.state.draggables[c1].stateDraggablesIndex > this.stateDraggablesIndex) {
                    this.state.draggables[c1].stateDraggablesIndex -= 1;
                }

                c1 += 1;
            }

            return;
        }

        this.containerEl.show();

        this.zIndex = 1;

        this.iconEl.detach();
        this.iconEl.css('border', 'none');
        this.iconEl.css('background-color', 'transparent');
        this.iconEl.css('padding-left', 0);
        this.iconEl.css('padding-right', 0);
        this.iconEl.css('z-index', this.zIndex);
        this.iconEl.css(
            'width',
            this.iconWidthSmall
        );
        this.iconEl.css(
            'height',
            this.iconHeightSmall
        );
        this.iconEl.css(
            'left',
            50 - this.iconWidthSmall * 0.5
        );
        if (this.labelEl !== null) {
            this.iconEl.css('top', 5);
        } else {
            this.iconEl.css(
                'top',
                50 - this.iconHeightSmall * 0.5
            );
        }

        this.iconEl.appendTo(this.containerEl);

        if (this.labelEl !== null) {
            this.labelEl.detach();
            this.labelEl.css('border', 'none');
            this.labelEl.css('background-color', 'transparent');
            this.labelEl.css('padding-left', 0);
            this.labelEl.css('padding-right', 0);
            this.labelEl.css('z-index', this.zIndex);
            this.labelEl.css(
                'left',
                50 - this.labelWidth * 0.5
            );
            this.labelEl.css(
                'top',
                5 + this.iconHeightSmall + 5
            );
            this.labelEl.appendTo(
                this.containerEl
            );
        }

        this.inContainer = true;
    }
});

// End of wrapper for RequireJS. As you can see, we are passing
// namespaced Require JS variables to an anonymous function. Within
// it, you can use the standard requirejs(), require(), and define()
// functions as if they were in the global namespace.
}(RequireJS.requirejs, RequireJS.require, RequireJS.define)); // End-of: (function (requirejs, require, define)
