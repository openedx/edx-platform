$(document).ready(function() {
    // making the unit list draggable. Note: sortable didn't work b/c it considered
    // drop points which the user hovered over as destinations and proactively changed
    // the dom; so, if the user subsequently dropped at an illegal spot, the reversion
    // point was the last dom change.
    $('.unit').draggable({
        axis: 'y',
        handle: '.drag-handle',
        zIndex: 999,
        start: initiateHesitate,
        // left 2nd arg in as inert selector b/c i was uncertain whether we'd try to get the shove up/down
        // to work in the future
        drag: generateCheckHoverState('.collapsed', ''),
        stop: removeHesitate,
        revert: "invalid"
    });

    // Subsection reordering
    $('.id-holder').draggable({
        axis: 'y',
        handle: '.section-item .drag-handle',
        zIndex: 999,
        start: initiateHesitate,
        drag: generateCheckHoverState('.courseware-section.collapsed', ''),
        stop: removeHesitate,
        revert: "invalid"
    });

    // Section reordering
    $('.courseware-section').draggable({
        axis: 'y',
        handle: 'header .drag-handle',
        stack: '.courseware-section',
        revert: "invalid"
    });


    $('.sortable-unit-list').droppable({
        accept : '.unit',
        greedy: true,
        tolerance: "pointer",
        hoverClass: "dropover",
        drop: onUnitReordered
    });
    $('.subsection-list > ol').droppable({
        // why don't we have a more useful class for subsections than id-holder?
        accept : '.id-holder', // '.unit, .id-holder',
        tolerance: "pointer",
        hoverClass: "dropover",
        drop: onSubsectionReordered,
        greedy: true
    });

    // Section reordering
    $('.courseware-overview').droppable({
        accept : '.courseware-section',
        tolerance: "pointer",
        drop: onSectionReordered,
        greedy: true
    });

    // stop clicks on drag bars from doing their thing w/o stopping drag
    $('.drag-handle').click(function(e) {e.preventDefault(); });

});

CMS.HesitateEvent.toggleXpandHesitation = null;
function initiateHesitate(event, ui) {
        CMS.HesitateEvent.toggleXpandHesitation = new CMS.HesitateEvent(expandSection, 'dragLeave', true);
        $('.collapsed').on('dragEnter', CMS.HesitateEvent.toggleXpandHesitation, CMS.HesitateEvent.toggleXpandHesitation.trigger);
        $('.collapsed, .unit, .id-holder').each(function() {
                this.proportions = {width : this.offsetWidth, height : this.offsetHeight };
                // reset b/c these were holding values from aborts
                this.isover = false;
        });
}

function computeIntersection(droppable, uiHelper, y) {
    /*
     * Test whether y falls within the bounds of the droppable on the Y axis
     */
    // NOTE: this only judges y axis intersection b/c that's all we're doing right now
    //  don't expand the thing being carried
    if (uiHelper.is(droppable)) {
        return null;
    }

    $.extend(droppable, {offset : $(droppable).offset()});

    var t = droppable.offset.top,
        b = t + droppable.proportions.height;

    if (t === b) {
        // probably wrong values b/c invisible at the time of caching
        droppable.proportions = { width : droppable.offsetWidth, height : droppable.offsetHeight };
        b = t + droppable.proportions.height;
    }
    //  equivalent to the intersects test
    return (t < y && // Bottom Half
                y  < b ); // Top Half
}

// NOTE: selectorsToShove is not currently being used but I left this code as it did work but not well
function generateCheckHoverState(selectorsToOpen, selectorsToShove) {
    return function(event, ui) {
        // copied from jquery.ui.droppable.js $.ui.ddmanager.drag & other ui.intersect
        var draggable = $(this).data("ui-draggable"),
            centerY = (draggable.positionAbs || draggable.position.absolute).top + (draggable.helperProportions.height / 2);
        $(selectorsToOpen).each(function() {
            var intersects = computeIntersection(this, ui.helper, centerY),
                c = !intersects && this.isover ? "isout" : (intersects && !this.isover ? "isover" : null);

            if(!c) {
                return;
            }

            this[c] = true;
            this[c === "isout" ? "isover" : "isout"] = false;
            $(this).trigger(c === "isover" ? "dragEnter" : "dragLeave");
        });

        $(selectorsToShove).each(function() {
            var intersectsBottom = computeIntersection(this, ui.helper, (draggable.positionAbs || draggable.position.absolute).top);

            if ($(this).hasClass('ui-dragging-pushup')) {
                if (!intersectsBottom) {
                     console.log('not up', $(this).data('id'));
                     $(this).removeClass('ui-dragging-pushup');
                 }
            }
            else if (intersectsBottom) {
                console.log('up', $(this).data('id'));
                $(this).addClass('ui-dragging-pushup');
            }

            var intersectsTop = computeIntersection(this, ui.helper,
                    (draggable.positionAbs || draggable.position.absolute).top + draggable.helperProportions.height);

            if ($(this).hasClass('ui-dragging-pushdown')) {
                if (!intersectsTop) {
                    console.log('not down', $(this).data('id'));
                    $(this).removeClass('ui-dragging-pushdown');
                }
            }
            else if (intersectsTop) {
                console.log('down', $(this).data('id'));
                $(this).addClass('ui-dragging-pushdown');
            }

        });
    };
}

function removeHesitate(event, ui) {
        $('.collapsed').off('dragEnter', CMS.HesitateEvent.toggleXpandHesitation.trigger);
        $('.ui-dragging-pushdown').removeClass('ui-dragging-pushdown');
        $('.ui-dragging-pushup').removeClass('ui-dragging-pushup');
        CMS.HesitateEvent.toggleXpandHesitation = null;
}

function expandSection(event) {
        $(event.delegateTarget).removeClass('collapsed', 400);
        // don't descend to icon's on children (which aren't under first child) only to this element's icon
        $(event.delegateTarget).children().first().find('.expand-collapse-icon').removeClass('expand', 400).addClass('collapse');
}

function onUnitReordered(event, ui) {
        // a unit's been dropped on this subsection,
        //       figure out where it came from and where it slots in.
        _handleReorder(event, ui, 'subsection-id', 'li:.leaf');
}

function onSubsectionReordered(event, ui) {
        // a subsection has been dropped on this section,
        //       figure out where it came from and where it slots in.
        _handleReorder(event, ui, 'section-id', 'li:.branch');
}

function onSectionReordered(event, ui) {
        // a section moved w/in the overall (cannot change course via this, so no parentage change possible, just order)
        _handleReorder(event, ui, 'course-id', '.courseware-section');
}

function _handleReorder(event, ui, parentIdField, childrenSelector) {
        // figure out where it came from and where it slots in.
        var subsection_id = $(event.target).data(parentIdField);
        var _els = $(event.target).children(childrenSelector);
        var children = _els.map(function(idx, el) { return $(el).data('id'); }).get();
        // if new to this parent, figure out which parent to remove it from and do so
        if (!_.contains(children, ui.draggable.data('id'))) {
                var old_parent = ui.draggable.parent();
                var old_children = old_parent.children(childrenSelector).map(function(idx, el) { return $(el).data('id'); }).get();
                old_children = _.without(old_children, ui.draggable.data('id'));
                $.ajax({
                        url: "/save_item",
                        type: "POST",
                        dataType: "json",
                        contentType: "application/json",
                        data:JSON.stringify({ 'id' : old_parent.data(parentIdField), 'children' : old_children})
                });
        }
        else {
                // staying in same parent
                // remove so that the replacement in the right place doesn't double it
                children = _.without(children, ui.draggable.data('id'));
        }
        // add to this parent (figure out where)
        for (var i = 0, bump = 0; i < _els.length; i++) {
            if (ui.draggable.is(_els[i])) {
                bump = -1; // bump indicates that the draggable was passed in the dom but not children's list b/c
                // it's not in that list
            }
            else if (ui.offset.top < $(_els[i]).offset().top) {
                        // insert at i in children and _els
                        ui.draggable.insertBefore($(_els[i]));
                        // TODO figure out correct way to have it remove the style: top:n; setting (and similar line below)
                        ui.draggable.attr("style", "position:relative;");
                        children.splice(i + bump, 0, ui.draggable.data('id'));
                        break;
                }
        }
        // see if it goes at end (the above loop didn't insert it)
        if (!_.contains(children, ui.draggable.data('id'))) {
                $(event.target).append(ui.draggable);
                ui.draggable.attr("style", "position:relative;"); // STYLE hack too
                children.push(ui.draggable.data('id'));
        }
        var saving = new CMS.Views.Notification.Mini({
            title: gettext('Saving') + '&hellip;'
        });
        saving.show();
        $.ajax({
                url: "/save_item",
                type: "POST",
                dataType: "json",
                contentType: "application/json",
                data:JSON.stringify({ 'id' : subsection_id, 'children' : children}),
                success: function() {
                    saving.hide();
                }
        });

}


