define(["domReady", "jquery", "jquery.ui", "gettext", "js/views/feedback_notification", "draggabilly"],
    function (domReady, $, ui, gettext, NotificationView, Draggabilly) {

        var overviewDragger = {
            droppableClasses: 'drop-target drop-target-prepend drop-target-before drop-target-after',
            validDropClass: "valid-drop",
            expandOnDropClass: "expand-on-drop",

            /*
             * Determine information about where to drop the currently dragged
             * element. Returns the element to attach to and the method of
             * attachment ('before', 'after', or 'prepend').
             */
            findDestination: function (ele, yChange) {
                var eleY = ele.offset().top;
                var containers = $(ele.data('droppable-class'));

                for (var i = 0; i < containers.length; i++) {
                    var container = $(containers[i]);
                    // Exclude the 'new unit' buttons, and make sure we don't
                    // prepend an element to itself
                    var siblings = container.children().filter(function () {
                        return $(this).data('id') !== undefined && !$(this).is(ele);
                    });
                    // If the container is collapsed, check to see if the
                    // element is on top of its parent list -- don't check the
                    // position of the container
                    var parentList = container.parents(ele.data('parent-location-selector')).first();
                    if (parentList.hasClass('collapsed')) {
                        if (Math.abs(eleY - parentList.offset().top) < 10) {
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
                        if (siblings.length == 0 &&
                            containerY != eleY &&
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
                                var siblingHeight = $sibling.height();
                                var siblingYEnd = siblingY + siblingHeight;

                                // Facilitate dropping into the beginning or end of a list
                                // (coming from opposite direction) via a "fudge factor". Math.min is for Jasmine test.
                                var fudge = Math.min(Math.ceil(siblingHeight / 2), 20);
                                // Dragging up into end of list.
                                if (j == siblings.length - 1 && yChange < 0 && Math.abs(eleY - siblingYEnd) <= fudge) {
                                    return {
                                        ele: $sibling,
                                        attachMethod: 'after'
                                    };
                                }
                                // Dragging down into beginning of list.
                                else if (j == 0 && yChange > 0 && Math.abs(eleY - siblingY) <= fudge) {
                                    return {
                                        ele: $sibling,
                                        attachMethod: 'before'
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
                // Failed drag
                return {
                    ele: null,
                    attachMethod: ''
                }
            },

            // Information about the current drag.
            dragState: {},

            onDragStart: function (draggie, event, pointer) {
                var ele = $(draggie.element);
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
                if (!ele.hasClass('collapsed')) {
                    ele.addClass('collapsed');
                    ele.find('.expand-collapse-icon').addClass('expand').removeClass('collapse');
                    // onDragStart gets called again after the collapse, so we can't just store a variable in the dragState.
                    ele.addClass(this.expandOnDropClass);
                }
            },

            onDragMove: function (draggie, event, pointer) {
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

                var yChange = draggie.dragPoint.y - this.dragState.lastY;
                if (yChange !== 0) {
                    this.dragState.direction = yChange;
                }
                this.dragState.lastY = draggie.dragPoint.y;

                var ele = $(draggie.element);
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

            onDragEnd: function (draggie, event, pointer) {
                var ele = $(draggie.element);
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

            pointerInBounds: function (pointer, ele) {
                return pointer.clientX >= ele.offset().left && pointer.clientX < ele.offset().left + ele.width();
            },

            expandElement: function (ele) {
                ele.removeClass('collapsed');
                ele.find('.expand-collapse-icon').removeClass('expand').addClass('collapse');
            },

            /*
             * Find all parent-child changes and save them.
             */
            handleReorder: function (ele) {
                var parentSelector = ele.data('parent-location-selector');
                var childrenSelector = ele.data('child-selector');
                var newParentEle = ele.parents(parentSelector).first();
                var newParentID = newParentEle.data('id');
                var oldParentID = ele.data('parent-id');
                // If the parent has changed, update the children of the old parent.
                if (oldParentID !== newParentID) {
                    // Find the old parent element.
                    var oldParentEle = $(parentSelector).filter(function () {
                        return $(this).data('id') === oldParentID;
                    });
                    this.saveItem(oldParentEle, childrenSelector, function () {
                        ele.data('parent-id', newParentID);
                    });
                }
                var saving = new NotificationView.Mini({
                    title: gettext('Saving&hellip;')
                });
                saving.show();
                ele.addClass('was-dropped');
                // Timeout interval has to match what is in the CSS.
                setTimeout(function () {
                    ele.removeClass('was-dropped');
                }, 1000);
                this.saveItem(newParentEle, childrenSelector, function () {
                    saving.hide();
                });
            },

            /*
             * Actually save the update to the server. Takes the element
             * representing the parent item to save, a CSS selector to find
             * its children, and a success callback.
             */
            saveItem: function (ele, childrenSelector, success) {
                // Find all current child IDs.
                var children = _.map(
                    ele.find(childrenSelector),
                    function (child) {
                        return $(child).data('id');
                    }
                );
                $.ajax({
                    url: '/save_item',
                    type: 'POST',
                    dataType: 'json',
                    contentType: 'application/json',
                    data: JSON.stringify({
                        id: ele.data('id'),
                        children: children
                    }),
                    success: success
                });
            },

            /*
             * Make `type` draggable using `handleClass`, able to be dropped
             * into `droppableClass`, and with parent type
             * `parentLocationSelector`.
             */
            makeDraggable: function (type, handleClass, droppableClass, parentLocationSelector) {
                _.each(
                    $(type),
                    function (ele) {
                        // Remember data necessary to reconstruct the parent-child relationships
                        $(ele).data('droppable-class', droppableClass);
                        $(ele).data('parent-location-selector', parentLocationSelector);
                        $(ele).data('child-selector', type);
                        var draggable = new Draggabilly(ele, {
                            handle: handleClass,
                            containment: '.wrapper-dnd'
                        });
                        draggable.on('dragStart', _.bind(overviewDragger.onDragStart, overviewDragger));
                        draggable.on('dragMove', _.bind(overviewDragger.onDragMove, overviewDragger));
                        draggable.on('dragEnd', _.bind(overviewDragger.onDragEnd, overviewDragger));
                    }
                );
            }
        };

        domReady(function() {
            // Section
            overviewDragger.makeDraggable(
                '.courseware-section',
                '.section-drag-handle',
                '.courseware-overview',
                'article.courseware-overview'
            );
            // Subsection
            overviewDragger.makeDraggable(
                '.id-holder',
                '.subsection-drag-handle',
                '.subsection-list > ol',
                '.courseware-section'
            );
            // Unit
            overviewDragger.makeDraggable(
                '.unit',
                '.unit-drag-handle',
                'ol.sortable-unit-list',
                'li.branch, article.subsection-body'
            );
        });

        return overviewDragger;
    });
