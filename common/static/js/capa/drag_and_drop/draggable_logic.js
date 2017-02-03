(function(requirejs, require, define) {
    define(['js/capa/drag_and_drop/update_input', 'js/capa/drag_and_drop/targets'], function(updateInput, Targets) {
        return {
            'moveDraggableTo': function(moveType, target, funcCallback) {
                var self, offset;

                if (this.hasLoaded === false) {
                    self = this;

                    setTimeout(function() {
                        self.moveDraggableTo(moveType, target, funcCallback);
                    }, 50);

                    return;
                }

                if ((this.isReusable === true) && (this.isOriginal === true)) {
                    this.makeDraggableCopy(function(draggableCopy) {
                        draggableCopy.moveDraggableTo(moveType, target, funcCallback);
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
                    'height': this.iconHeight
                });
                if (moveType === 'target') {
                    this.iconEl.css({
                        'left': target.offset.left + 0.5 * target.w - this.iconWidth * 0.5 + offset - this.iconElLeftOffset,
                        'top': target.offset.top + 0.5 * target.h - this.iconHeight * 0.5 + offset
                    });
                } else {
                    this.iconEl.css({
                        'left': target.x - this.iconWidth * 0.5 + offset - this.iconElLeftOffset,
                        'top': target.y - this.iconHeight * 0.5 + offset
                    });
                }
                this.iconEl.appendTo(this.state.baseImageEl.parent());

                if (this.labelEl !== null) {
                    if (this.isOriginal === true) {
                        this.labelEl.detach();
                    }
                    this.labelEl.css({
                        'background-color': this.state.config.labelBgColor,
                        'padding-left': 8,
                        'padding-right': 8,
                        'border': '1px solid black'
                    });
                    if (moveType === 'target') {
                        this.labelEl.css({
                            'left': target.offset.left + 0.5 * target.w - this.labelWidth * 0.5 + offset - 9, // Account for padding, border.
                            'top': target.offset.top + 0.5 * target.h + this.iconHeight * 0.5 + 5 + offset
                        });
                    } else {
                        this.labelEl.css({
                            'left': target.x - this.labelWidth * 0.5 + offset - 9, // Account for padding, border.
                            'top': target.y - this.iconHeight * 0.5 + this.iconHeight + 5 + offset
                        });
                    }
                    this.labelEl.appendTo(this.state.baseImageEl.parent());
                }

                if (moveType === 'target') {
                    target.addDraggable(this);
                } else {
                    this.x = target.x;
                    this.y = target.y;
                }

                this.zIndex = 1000;
                this.correctZIndexes();

                Targets.initializeTargetField(this);

                if (this.isOriginal === true) {
                    this.state.numDraggablesInSlider -= 1;
                    this.state.updateArrowOpacity();
                }

                if ($.isFunction(funcCallback) === true) {
                    funcCallback();
                }
            },

    // At this point the mouse was realeased, and we need to check
    // where the draggable eneded up. Based on several things, we
    // will either move the draggable back to the slider, or update
    // the input with the user's answer (X-Y position of the draggable,
    // or the ID of the target where it landed.
            'checkLandingElement': function() {
                var positionIE;

                this.mousePressed = false;
                positionIE = this.iconEl.position();

                if (this.state.config.individualTargets === true) {
                    if (this.checkIfOnTarget(positionIE) === true) {
                        this.correctZIndexes();

                        Targets.initializeTargetField(this);
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

                        Targets.initializeTargetField(this);
                    }
                }

                if (this.isOriginal === true) {
                    this.state.updateArrowOpacity();
                }
                updateInput.update(this.state);
            },

    // Determine if a draggable, after it was relased, ends up on a
    // target. We do this by iterating over all of the targets, and
    // for each one we check whether the draggable's center is
    // within the target's dimensions.
    //
    // positionIE is the object as returned by
    //
    //     this.iconEl.position()
            'checkIfOnTarget': function(positionIE) {
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

            // If the target is on a draggable (from target field), we must make sure that
            // this draggable is not the same as "this" one.
                    if ((target.type === 'on_drag') && (target.draggableObj.uniqueId === this.uniqueId)) {
                        continue;
                    }

            // Check if the draggable's center coordinate is within
            // the target's dimensions. If not, go to next target.
                    if (
                (positionIE.top + this.iconHeight * 0.5 < target.offset.top) ||
                (positionIE.top + this.iconHeight * 0.5 > target.offset.top + target.h) ||
                (positionIE.left + this.iconWidth * 0.5 < target.offset.left) ||
                (positionIE.left + this.iconWidth * 0.5 > target.offset.left + target.w)
            ) {
                        continue;
                    }

            // If the draggable was moved from one target to
            // another, then we need to remove it from the
            // previous target's draggables list, and add it to the
            // new target's draggables list.
                    if ((this.onTarget !== null) && (this.onTarget.uniqueId !== target.uniqueId)) {
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
            },

            'toggleTargets': function(isEnabled) {
                var effect = isEnabled ? 'move' : null;

                this.state.baseImageEl.attr('aria-dropeffect', effect);
                $.each(this.state.targets, function(index, target) {
                    target.targetEl.attr('aria-dropeffect', effect);
                });
            },

            'snapToTarget': function(target) {
                var offset;

                offset = 0;
                if (this.state.config.targetOutline === true) {
                    offset = 1;
                }

                this.iconEl.css({
                    'left': target.offset.left + 0.5 * target.w - this.iconWidth * 0.5 + offset - this.iconElLeftOffset,
                    'top': target.offset.top + 0.5 * target.h - this.iconHeight * 0.5 + offset
                });

                if (this.labelEl !== null) {
                    this.labelEl.css({
                        'left': target.offset.left + 0.5 * target.w - this.labelWidth * 0.5 + offset - 9, // Acoount for padding, border.
                        'top': target.offset.top + 0.5 * target.h + this.iconHeight * 0.5 + 5 + offset
                    });
                }
            },

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
            'correctZIndexes': function() {
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
            },

    // If a draggable was released in a wrong positione, we will
    // move it back to the slider, placing it in the same position
    // that it was dragged out of.
            'moveBackToSlider': function() {
                var c1;

                Targets.destroyTargetField(this);

                if (this.isOriginal === false) {
                    this.iconEl.remove();
                    if (this.labelEl !== null) {
                        this.labelEl.remove();
                    }

                    this.state.draggables.splice(this.stateDraggablesIndex, 1);

                    for (c1 = 0; c1 < this.state.draggables.length; c1 += 1) {
                        if (this.state.draggables[c1].stateDraggablesIndex > this.stateDraggablesIndex) {
                            this.state.draggables[c1].stateDraggablesIndex -= 1;
                        }
                    }

                    return;
                }

                this.containerEl.show();
                this.zIndex = 1;

                this.iconEl.detach();
                if (this.iconImgEl !== null) {
                    this.iconImgEl.css({
                        'width': this.iconWidthSmall,
                        'height': this.iconHeightSmall
                    });
                }
                this.iconEl.css({
                    'border': 'none',
                    'background-color': 'transparent',
                    'padding-left': 0,
                    'padding-right': 0,
                    'z-index': this.zIndex,
                    'width': this.iconWidthSmall,
                    'height': this.iconHeightSmall,
                    'left': 50 - this.iconWidthSmall * 0.5,

            // Before:
            // 'top': ((this.labelEl !== null) ? (100 - this.iconHeightSmall - 25) * 0.5 : 50 - this.iconHeightSmall * 0.5)
            // After:
                    'top': ((this.labelEl !== null) ? 37.5 : 50.0) - 0.5 * this.iconHeightSmall
                });
                this.iconEl.appendTo(this.containerEl);

                if (this.labelEl !== null) {
                    this.labelEl.detach();
                    this.labelEl.css({
                        'border': 'none',
                        'background-color': 'transparent',
                        'padding-left': 0,
                        'padding-right': 0,
                        'z-index': this.zIndex,
                        'left': 50 - this.labelWidth * 0.5,

                // Before:
                // 'top': (100 - this.iconHeightSmall - 25) * 0.5 + this.iconHeightSmall + 5
                // After:
                        'top': 42.5 + 0.5 * this.iconHeightSmall
                    });
                    this.labelEl.appendTo(this.containerEl);
                }

                this.inContainer = true;
            }
        }; // End-of: return {
    }); // End-of: define(['update_input', 'targets'], function (updateInput, Targets) {
}(RequireJS.requirejs, RequireJS.require, RequireJS.define)); // End-of: (function (requirejs, require, define) {
