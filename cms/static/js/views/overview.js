$(document).ready(function() {

    // Section
    makeDraggable(
        '.courseware-section',
        'a.section-drag-handle',
        '.courseware-overview',
        'article.courseware-overview'
    );
    // Subsection
    makeDraggable(
        '.id-holder',
        'a.subsection-drag-handle',
        '.subsection-list > ol',
        '.subsection-list > ol'
    );
    // Unit
    makeDraggable(
        '.unit',
        'a.unit-drag-handle',
        '.sortable-unit-list',
        'li.branch'
    );

    /*
     * Make `type` draggable using `handleClass`, and able to be
     * dropped into `droppableClass`.
     */
    function makeDraggable(type, handleClass, droppableClass, parentLocationSelector) {
        _.each(
            $(type),
            function(ele) {
                // Remember data necessary to reconstruct the parent-child relationships
                $(ele).data('droppable-class', droppableClass);
                $(ele).data('parent-location-selector', parentLocationSelector);
                $(ele).data('child-selector', type);
                var draggable = new Draggabilly(ele, {
                    handle: handleClass,
                    axis: 'y'
                });
                draggable.on('dragStart', onDragStart);
                draggable.on('dragMove', onDragMove);
                draggable.on('dragEnd', onDragEnd);
            }
        );
    }

    /*
     * Determine information about where to drop the currently dragged
     * element. Returns the element to attach to and the method of
     * attachment ('before', 'after', or 'prepend').
     */
    function findDestination(ele) {
        var eleY = ele.offset().top;
        var containers = $(ele.data('droppable-class'));

        for(var i = 0; i < containers.length; i++) {
            var container = $(containers[i]);
            // Exclude the 'new unit' buttons, and make sure we don't
            // prepend an element to itself
            var siblings = container.children().filter(function () {
                return $(this).data('id') !== undefined && !$(this).is(ele);
            });
            // If the list is empty, we should prepend to it
            if(siblings.length == 0) {
                if(Math.abs(eleY - container.offset().top) < 50) {
                    return {
                        ele: container,
                        attachMethod: 'prepend'
                    };
                }
            }
            // Otherwise the list is populated, and we should attach before/after a sibling
            else {
                for(var j = 0; j < siblings.length; j++) {
                    var $sibling = $(siblings[j]);
                    var siblingHeight = $sibling.height();
                    var siblingY = $sibling.offset().top;

                    if(Math.abs(eleY - siblingY) < siblingHeight) {
                        return {
                            ele: $sibling,
                            attachMethod: siblingY > eleY ? 'before' : 'after'
                        };
                    }
                }
            }
        }

        // Failed drag
        return {
            ele: null,
            attachMethod: ''
        };
    }

    // Information about the current drag.
    var dragState = {};

    function onDragStart(draggie, event, pointer) {
        var ele = $(draggie.element);
        dragState = {
            // Where we started, in case of a failed drag
            offset: ele.offset(),
            // Which element will be dropped into/onto on success
            dropDestination: null
        };
    }

    function onDragMove(draggie, event, pointer) {
        var ele = $(draggie.element);
        var currentReplacement = findDestination(ele).ele;
        // Clear out the old destination
        if(dragState.dropDestination) {
            dragState.dropDestination.removeClass('drop-destination');
        }
        // Mark the new destination
        if(currentReplacement) {
            currentReplacement.addClass('drop-destination');
            dragState.dropDestination = currentReplacement;
        }
    }

    function onDragEnd(draggie, event, pointer) {
        var ele = $(draggie.element);

        var intersect = findDestination(ele);
        var destination = intersect.ele;
        var method = intersect.attachMethod;

        // If the drag succeeded, rearrange the DOM and send the result.
        if(destination) {
            destination[method](ele);
            handleReorder(ele);
        }

        // Everything in its right place
        ele.css({
            top: 'auto',
            left: 'auto'
        });

        // Clear dragging state in preparation for the next event.
        if(dragState.dropDestination) {
            dragState.dropDestination.removeClass('drop-destination');
        }
        dragState = {};
    }

    /*
     * Find all parent-child changes and save them.
     */
    function handleReorder(ele) {
        var itemID = ele.data('id');
        var parentSelector = ele.data('parent-location-selector');
        var childrenSelector = ele.data('child-selector');
        var newParentEle = ele.parents(parentSelector).first();
        var newParentID = newParentEle.data('id');
        var oldParentID = ele.data('parent-id');
        // If the parent has changed, update the children of the old parent.
        if(oldParentID !== newParentID) {
            // Find the old parent element.
            var oldParentEle = $(parentSelector).filter(function() {
                return $(this).data('id') === oldParentID;
            });
            saveItem(oldParentEle, childrenSelector, function() {
                ele.data('parent-id', newParentID);
            });
        }
        var saving = new CMS.Views.Notification.Mini({
            title: gettext('Saving&hellip;')
        });
        saving.show();
        saveItem(newParentEle, childrenSelector, function() {
            saving.hide();
        });
    }

    /*
     * Actually save the update to the server. Takes the element
     * representing the parent item to save, a CSS selector to find
     * its children, and a success callback.
     */
    function saveItem(ele, childrenSelector, success) {
        // Find all current child IDs.
        var children = _.map(
            ele.find(childrenSelector),
            function(child) {
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
    }
});
