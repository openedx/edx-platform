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
        drag: checkHoverState,
        stop: removeHesitate,
        revert: "invalid"
    });
    
    // Subsection reordering
    $('.id-holder').draggable({
        axis: 'y',
        handle: '.section-item .drag-handle',
        zIndex: 999,  
        start: initiateHesitate,
        drag: checkHoverState,
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
    
});


CMS.HesitateEvent.toggleXpandHesitation = null;
function initiateHesitate(event, ui) {
        CMS.HesitateEvent.toggleXpandHesitation = new CMS.HesitateEvent(expandSection, 'dragLeave', true);
        $('.collapsed').on('dragEnter', CMS.HesitateEvent.toggleXpandHesitation, CMS.HesitateEvent.toggleXpandHesitation.trigger);
        $('.collapsed').each(function() {
                this.proportions = {width : this.offsetWidth, height : this.offsetHeight };
                // reset b/c these were holding values from aborts
                this.isover = false;
        });
}
function checkHoverState(event, ui) {
        // copied from jquery.ui.droppable.js $.ui.ddmanager.drag & other ui.intersect
        var draggable = $(this).data("ui-draggable"),
                x1 = (draggable.positionAbs || draggable.position.absolute).left + (draggable.helperProportions.width / 2), 
                y1 = (draggable.positionAbs || draggable.position.absolute).top + (draggable.helperProportions.height / 2);
        $('.collapsed').each(function() {
                // don't expand the thing being carried
                if (ui.helper.is(this)) {
                        return;
                }
                
                $.extend(this, {offset : $(this).offset()});

                var droppable = this,
                        l = droppable.offset.left, 
                        r = l + droppable.proportions.width,
                        t = droppable.offset.top, 
                        b = t + droppable.proportions.height;
                
                if (l === r) {
                        // probably wrong values b/c invisible at the time of caching
                        droppable.proportions = { width : droppable.offsetWidth, height : droppable.offsetHeight };
                        r = l + droppable.proportions.width;
                        b = t + droppable.proportions.height;
                }
                // equivalent to the intersects test
                var intersects = (l < x1  && // Right Half
                                        x1  < r && // Left Half
                                        t < y1 && // Bottom Half
                                        y1  < b ), // Top Half

                        c = !intersects && this.isover ? "isout" : (intersects && !this.isover ? "isover" : null);
                        
                if(!c) {
                        return;
                }

                this[c] = true;
                this[c === "isout" ? "isover" : "isout"] = false;
                $(this).trigger(c === "isover" ? "dragEnter" : "dragLeave");
        });
}
function removeHesitate(event, ui) {
        $('.collapsed').off('dragEnter', CMS.HesitateEvent.toggleXpandHesitation.trigger);
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
        for (var i = 0; i < _els.length; i++) {
                if (!ui.draggable.is(_els[i]) && ui.offset.top < $(_els[i]).offset().top) {
                        // insert at i in children and _els
                        ui.draggable.insertBefore($(_els[i]));
                        // TODO figure out correct way to have it remove the style: top:n; setting (and similar line below)
                        ui.draggable.attr("style", "position:relative;");
                        children.splice(i, 0, ui.draggable.data('id'));
                        break;
                }
        }
        // see if it goes at end (the above loop didn't insert it)
        if (!_.contains(children, ui.draggable.data('id'))) {
                $(event.target).append(ui.draggable);
                ui.draggable.attr("style", "position:relative;"); // STYLE hack too
                children.push(ui.draggable.data('id'));
        }
        $.ajax({
                url: "/save_item",
                type: "POST",
                dataType: "json",
                contentType: "application/json",
                data:JSON.stringify({ 'id' : subsection_id, 'children' : children})
        });

}
