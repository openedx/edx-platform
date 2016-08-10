define(['jquery', 'jquery.ui', 'underscore', 'gettext', 'draggabilly',
        'js/utils/module', 'common/js/components/views/feedback_notification'],
    function($, ui, _, gettext, Draggabilly, ModuleUtils, NotificationView) {
        'use strict';

        var contentDragger = {
            droppableClasses: 'drop-target drop-target-prepend drop-target-before drop-target-after',
            validDropClass: 'valid-drop',
            expandOnDropClass: 'expand-on-drop',
            collapsedClass: 'is-collapsed',

            /*
             * Determine information about where to drop the currently dragged
             * element. Returns the element to attach to and the method of
             * attachment ('before', 'after', or 'prepend').
             */
            findDestination: function(ele, yChange) {
                var eleY = ele.offset().top;
                var eleYEnd = eleY + ele.outerHeight();
                var containers = $(ele.data('droppable-class'));
                var isSibling = function() {
                    return $(this).data('locator') !== undefined && !$(this).is(ele);
                };

                for (var i = 0; i < containers.length; i++) {
                    var container = $(containers[i]);
                    // Exclude the 'new unit' buttons, and make sure we don't
                    // prepend an element to itself
                    var siblings = container.children().filter(isSibling);
                    // If the container is collapsed, check to see if the
                    // element is on top of its parent list -- don't check the
                    // position of the container
                    var parentList = container.parents(ele.data('parent-location-selector')).first();
                    if (parentList.hasClass(this.collapsedClass)) {
                        var parentListTop = parentList.offset().top;
                        // To make it easier to drop subsections into collapsed sections (which have
                        // a lot of visual padding around them), allow a fudge factor around the
                        // parent element.
                        var collapseFudge = 10;
                        if (Math.abs(eleY - parentListTop) < collapseFudge ||
                            (eleY > parentListTop &&
                            eleYEnd - collapseFudge <= parentListTop + parentList.outerHeight())
                        ) {
                            return {
                                ele: container,
                                attachMethod: 'prepend',
                                parentList: parentList
                            };
                        }
                    }
                    // Otherwise, do check the container
                    else {
                        // If the list is empty, we should prepend to it,
                        // unless both elements are at the same location --
                        // this prevents the user from being unable to expand
                        // a section
                        var containerY = container.offset().top;
                        if (siblings.length === 0 &&
                            containerY !== eleY &&
                            Math.abs(eleY - containerY) < 50) {
                            return {
                                ele: container,
                                attachMethod: 'prepend'
                            };
                        }
                        // Otherwise the list is populated, and we should attach before/after a sibling
                        else {
                            for (var j = 0; j < siblings.length; j++) {
                                var $sibling = $(siblings[j]);
                                var siblingY = $sibling.offset().top;
                                var siblingHeight = $sibling.outerHeight();
                                var siblingYEnd = siblingY + siblingHeight;

                                // Facilitate dropping into the beginning or end of a list
                                // (coming from opposite direction) via a "fudge factor". Math.min is for Jasmine test.
                                var fudge = Math.min(Math.ceil(siblingHeight / 2), 35);

                                // Dragging to top or bottom of a list with only one element is tricky
                                // because the element being dragged may be the same size as the sibling.
                                if (siblings.length === 1) {
                                    // Element being dragged is within the drop target. Use the direction
                                    // of the drag (yChange) to determine before or after.
                                    if (eleY + fudge >= siblingY && eleYEnd - fudge <= siblingYEnd) {
                                        return {
                                            ele: $sibling,
                                            attachMethod: yChange > 0 ? 'after' : 'before'
                                        };
                                    }
                                    // Element being dragged is before the drop target.
                                    else if (Math.abs(eleYEnd - siblingY) <= fudge) {
                                        return {
                                            ele: $sibling,
                                            attachMethod: 'before'
                                        };
                                    }
                                    // Element being dragged is after the drop target.
                                    else if (Math.abs(eleY - siblingYEnd) <= fudge) {
                                        return {
                                            ele: $sibling,
                                            attachMethod: 'after'
                                        };
                                    }
                                }
                                else {
                                    // Dragging up into end of list.
                                    if (j === siblings.length - 1 && yChange < 0 &&
                                        Math.abs(eleY - siblingYEnd) <= fudge) {
                                        return {
                                            ele: $sibling,
                                            attachMethod: 'after'
                                        };
                                    }
                                    // Dragging up or down into beginning of list.
                                    else if (j === 0 && Math.abs(eleY - siblingY) <= fudge) {
                                        return {
                                            ele: $sibling,
                                            attachMethod: 'before'
                                        };
                                    }
                                    // Dragging down into end of list. Special handling required because
                                    // the element being dragged may be taller then the element being dragged over
                                    // (if eleY can never be >= siblingY, general case at the end does not work).
                                    else if (j === siblings.length - 1 && yChange > 0 &&
                                        Math.abs(eleYEnd - siblingYEnd) <= fudge) {
                                        return {
                                            ele: $sibling,
                                            attachMethod: 'after'
                                        };
                                    }
                                    else if (eleY >= siblingY && eleY <= siblingYEnd) {
                                        return {
                                            ele: $sibling,
                                            attachMethod: eleY - siblingY <= siblingHeight / 2 ? 'before' : 'after'
                                        };
                                    }
                                }
                            }
                        }
                    }
                }
                // Failed drag
                return {
                    ele: null,
                    attachMethod: ''
                };
            },

            // Information about the current drag.
            dragState: {},

            onDragStart: function(draggable) {
                var ele = $(draggable.element);
                this.dragState = {
                    // Which element will be dropped into/onto on success
                    dropDestination: null,
                    // How we attach to the destination: 'before', 'after', 'prepend'
                    attachMethod: '',
                    // If dragging to an empty section, the parent section
                    parentList: null,
                    // The y location of the last dragMove event (to determine direction).
                    lastY: 0,
                    // The direction the drag is moving in (negative means up, positive down).
                    dragDirection: 0
                };
                if (!ele.hasClass(this.collapsedClass)) {
                    ele.addClass(this.collapsedClass);
                    ele.find('.expand-collapse').first().addClass('expand').removeClass('collapse');

                    // onDragStart gets called again after the collapse, so we can't
                    // just store a variable in the dragState.
                    ele.addClass(this.expandOnDropClass);
                }

                // We should remove this class name before start dragging to
                // avoid performance issues.
                ele.removeClass('was-dragging');
            },

            onDragMove: function(draggable, event, pointer) {
                // Handle scrolling of the browser.
                var scrollAmount = 0;
                var dragBuffer = 10;
                if (window.innerHeight - dragBuffer < pointer.clientY) {
                    scrollAmount = dragBuffer;
                }
                else if (dragBuffer > pointer.clientY) {
                    scrollAmount = -(dragBuffer);
                }
                if (scrollAmount !== 0) {
                    window.scrollBy(0, scrollAmount);
                    return;
                }

                var yChange = draggable.dragPoint.y - this.dragState.lastY;
                if (yChange !== 0) {
                    this.dragState.direction = yChange;
                }
                this.dragState.lastY = draggable.dragPoint.y;

                var ele = $(draggable.element);
                var destinationInfo = this.findDestination(ele, this.dragState.direction);
                var destinationEle = destinationInfo.ele;
                this.dragState.parentList = destinationInfo.parentList;

                // Clear out the old destination
                if (this.dragState.dropDestination) {
                    this.dragState.dropDestination.removeClass(this.droppableClasses);
                }
                // Mark the new destination
                if (destinationEle && this.pointerInBounds(pointer, ele)) {
                    ele.addClass(this.validDropClass);
                    destinationEle.addClass('drop-target drop-target-' + destinationInfo.attachMethod);
                    this.dragState.attachMethod = destinationInfo.attachMethod;
                    this.dragState.dropDestination = destinationEle;
                }
                else {
                    ele.removeClass(this.validDropClass);
                    this.dragState.attachMethod = '';
                    this.dragState.dropDestination = null;
                }
            },

            onDragEnd: function(draggable, event, pointer) {
                var ele = $(draggable.element);
                var destination = this.dragState.dropDestination;

                // Clear dragging state in preparation for the next event.
                if (destination) {
                    destination.removeClass(this.droppableClasses);
                }
                ele.removeClass(this.validDropClass);

                // If the drag succeeded, rearrange the DOM and send the result.
                if (destination && this.pointerInBounds(pointer, ele)) {
                    // Make sure we don't drop into a collapsed element
                    if (this.dragState.parentList) {
                        this.expandElement(this.dragState.parentList);
                    }
                    var method = this.dragState.attachMethod;
                    destination[method](ele);
                    this.handleReorder(ele);
                }
                // If the drag failed, send it back
                else {
                    $('.was-dragging').removeClass('was-dragging');
                    ele.addClass('was-dragging');
                }

                if (ele.hasClass(this.expandOnDropClass)) {
                    this.expandElement(ele);
                    ele.removeClass(this.expandOnDropClass);
                }

                // Everything in its right place
                ele.css({
                    top: 'auto',
                    left: 'auto'
                });

                this.dragState = {};
            },

            pointerInBounds: function(pointer, ele) {
                return pointer.clientX >= ele.offset().left && pointer.clientX < ele.offset().left + ele.outerWidth();
            },

            expandElement: function(ele) {
                // Verify all children of the element are rendered.
                var ensureChildrenRendered = ele.data('ensureChildrenRendered');
                if (_.isFunction(ensureChildrenRendered)) { ensureChildrenRendered(); }
                // Update classes.
                ele.removeClass(this.collapsedClass);
                ele.find('.expand-collapse').first().removeClass('expand').addClass('collapse');
            },

            /*
             * Find all parent-child changes and save them.
             */
            handleReorder: function(element) {
                var parentSelector = element.data('parent-location-selector'),
                    childrenSelector = element.data('child-selector'),
                    newParentEle = element.parents(parentSelector).first(),
                    newParentLocator = newParentEle.data('locator'),
                    oldParentLocator = element.data('parent'),
                    oldParentEle, saving, refreshParent;

                refreshParent = function(element) {
                    var refresh = element.data('refresh');
                    // If drop was into a collapsed parent, the parent will have been
                    // expanded. Views using this class may need to track the
                    // collapse/expand state, so send it with the refresh callback.
                    var collapsed = element.hasClass(contentDragger.collapsedClass);
                    if (_.isFunction(refresh)) { refresh(collapsed); }
                };
                saving = new NotificationView.Mini({
                    title: gettext('Saving')
                });
                saving.show();
                element.addClass('was-dropped');
                // Timeout interval has to match what is in the CSS.
                setTimeout(function() {
                    element.removeClass('was-dropped');
                }, 1000);
                this.saveItem(newParentEle, childrenSelector, function() {
                    saving.hide();

                    // Refresh new parent.
                    refreshParent(newParentEle);

                    // Refresh old parent.
                    if (newParentLocator !== oldParentLocator) {
                        oldParentEle = $(parentSelector).filter(function() {
                            return $(this).data('locator') === oldParentLocator;
                        });
                        refreshParent(oldParentEle);
                        element.data('parent', newParentLocator);
                    }
                });
            },

            /*
             * Actually save the update to the server. Takes the element
             * representing the parent item to save, a CSS selector to find
             * its children, and a success callback.
             */
            saveItem: function(ele, childrenSelector, success) {
                // Find all current child IDs.
                var children = _.map(
                    ele.find(childrenSelector),
                    function(child) {
                        return $(child).data('locator');
                    }
                );
                $.ajax({
                    url: ModuleUtils.getUpdateUrl(ele.data('locator')),
                    type: 'PUT',
                    dataType: 'json',
                    contentType: 'application/json',
                    data: JSON.stringify({
                        children: children
                    }),
                    success: success
                });
            },

            /*
             * Make DOM element with class `type` draggable using `handleClass`, able to be dropped
             * into `droppableClass`, and with parent type `parentLocationSelector`.
             * @param {DOM element, jQuery element} element
             * @param {Object} options The list of options. Possible options:
             *   `type` - class name of the element.
             *   `handleClass` - specifies on what element the drag interaction starts.
             *   `droppableClass` - specifies on what elements draggable element can be dropped.
             *   `parentLocationSelector` - class name of a parent element with data-locator.
             *   `refresh` - method that will be called after dragging to refresh
             *      views of the target and source xblocks.
             */
            makeDraggable: function(element, options) {
                var draggable;
                options = _.defaults({
                    type: undefined,
                    handleClass: undefined,
                    droppableClass: undefined,
                    parentLocationSelector: undefined,
                    refresh: undefined,
                    ensureChildrenRendered: undefined
                }, options);

                if ($(element).data('droppable-class') !== options.droppableClass) {
                    $(element).data({
                        'droppable-class': options.droppableClass,
                        'parent-location-selector': options.parentLocationSelector,
                        'child-selector': options.type,
                        'refresh': options.refresh,
                        'ensureChildrenRendered': options.ensureChildrenRendered
                    });

                    draggable = new Draggabilly(element, {
                        handle: options.handleClass,
                        containment: '.wrapper-dnd'
                    });
                    draggable.on('dragStart', _.bind(contentDragger.onDragStart, contentDragger, draggable));
                    draggable.on('dragMove', _.bind(contentDragger.onDragMove, contentDragger, draggable));
                    draggable.on('dragEnd', _.bind(contentDragger.onDragEnd, contentDragger, draggable));
                }
            }
        };

        return contentDragger;
    });
