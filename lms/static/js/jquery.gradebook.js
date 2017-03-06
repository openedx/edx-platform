


var Gradebook = function($element) {
    "use strict";
    var $body = $('body');
    var $grades = $element.find('.grades');
    var $studentTable = $element.find('.student-table');
    var $gradeTable = $element.find('.grade-table');
    var $search = $element.find('.student-search-field');
    var $leftShadow = $('<div class="left-shadow"></div>');
    var $rightShadow = $('<div class="right-shadow"></div>');
    var tableHeight = $gradeTable.height();
    var maxScroll = $gradeTable.width() - $grades.width();

    var mouseOrigin;
    var tableOrigin;

    var startDrag = function(e) {
        mouseOrigin = e.pageX;
        tableOrigin = $gradeTable.position().left;
        $body.addClass('no-select');
        $body.bind('mousemove', onDragTable);
        $body.bind('mouseup', stopDrag);
    };

    /**
     * - Called when the user drags the gradetable
     * - Calculates targetLeft, which is the desired position 
     *   of the grade table relative to its leftmost position, using:
     *   - the new x position of the user's mouse pointer;
     *   - the gradebook's current x position, and;
     *   - the value of maxScroll (gradetable width - container width).
     * - Updates the position and appearance of the gradetable.
     */
    var onDragTable = function(e) {
        var offset = e.pageX - mouseOrigin;
        var targetLeft = clamp(tableOrigin + offset, maxScroll, 0);
        updateHorizontalPosition(targetLeft);
        setShadows(targetLeft);
    };

    var stopDrag = function() {
        $body.removeClass('no-select');
        $body.unbind('mousemove', onDragTable);
        $body.unbind('mouseup', stopDrag);
    };

    var setShadows = function(left) {
        var padding = 30;

        var leftPercent = clamp(-left / padding, 0, 1);
        $leftShadow.css('opacity', leftPercent);

        var rightPercent = clamp((maxScroll + left) / padding, 0, 1);
        $rightShadow.css('opacity', rightPercent);
    };

    var clamp = function(val, min, max) {
        if(val > max) { return max; }
        if(val < min) { return min; }
        return val;
    };

    /**
     * - Called when the browser window is resized.
     * - Recalculates maxScroll (gradetable width - container width).
     * - Calculates targetLeft, which is the desired position
     *   of the grade table relative to its leftmost position, using:
     *   - the gradebook's current x position, and:
     *   - the new value of maxScroll
     * - Updates the position and appearance of the gradetable.
     */
    var onResizeTable = function() {
        maxScroll = $gradeTable.width() - $grades.width();
        var targetLeft = clamp($gradeTable.position().left, maxScroll, 0);
        updateHorizontalPosition(targetLeft);
        setShadows(targetLeft);
    };

    /**
     * - Called on table drag and on window (table) resize.
     * - Takes a integer value for the desired (pixel) offset from the left
     *   (zero/origin) position of the grade table.
     * - Uses that value to position the table relative to its leftmost
     *   possible position within its container.
     *
     *   @param {Number} left - The desired pixel offset from left of the
     *     desired position. If the value is 0, the gradebook should be moved 
     *     all the way to the left side relative to its parent container.
     */
    var updateHorizontalPosition = function(left) {
        $grades.scrollLeft(left);
    };

    var highlightRow = function() {
        $element.find('.highlight').removeClass('highlight');

        var index = $(this).index();
        $studentTable.find('tr').eq(index + 1).addClass('highlight');
        $gradeTable.find('tr').eq(index + 1).addClass('highlight');
    };

    var filter = function() {
        var term = $(this).val();
        if(term.length > 0) {
            $studentTable.find('tbody tr').hide();
            $gradeTable.find('tbody tr').hide();
            $studentTable.find('tbody tr:contains(' + term + ')').each(function() {
                $(this).show();
                $gradeTable.find('tr').eq($(this).index() + 1).show();
            });
        } else {
            $studentTable.find('tbody tr').show();
            $gradeTable.find('tbody tr').show();
        }
    };

    $leftShadow.css('height', tableHeight + 'px');
    $grades.append($leftShadow).append($rightShadow);
    setShadows(0);
    $grades.css('height', tableHeight);
    $gradeTable.bind('mousedown', startDrag);
    $element.find('tr').bind('mouseover', highlightRow);
    $search.bind('keyup', filter);
    $(window).bind('resize', onResizeTable);
};




