


var Gradebook = function($element) {
	var _this = this;
	var $element = $element;
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
		$body.css('-webkit-user-select', 'none');
		$body.bind('mousemove', moveDrag);
		$body.bind('mouseup', stopDrag);
	};

	var moveDrag = function(e) {
		var offset = e.pageX - mouseOrigin;
		var targetLeft = clamp(tableOrigin + offset, -maxScroll, 0);

		updateHorizontalPosition(targetLeft);

		setShadows(targetLeft);
	};

	var stopDrag = function(e) {
		$body.css('-webkit-user-select', 'auto');
		$body.unbind('mousemove', moveDrag);
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
	    if(val > max) return max;
	    if(val < min) return min;
	    return val;
	};

	var updateWidths = function(e) {
		maxScroll = $gradeTable.width() - $grades.width();
		var targetLeft = clamp($gradeTable.position().left, -maxScroll, 0);
		updateHorizontalPosition(targetLeft);
		setShadows(targetLeft);
	};

	var updateHorizontalPosition = function(left) {
		$gradeTable.css({
			'left': left + 'px'
		});
	};

	var highlightRow = function(e) {
		$element.find('.highlight').removeClass('highlight');

		var index = $(this).index();
		$studentTable.find('tr').eq(index + 1).addClass('highlight');
		$gradeTable.find('tr').eq(index + 1).addClass('highlight');
	};

	var filter = function(e) {
		var term = $(this).val();
		if(term.length > 0) {
			$studentTable.find('tbody tr').hide();
			$gradeTable.find('tbody tr').hide();
			$studentTable.find('tbody tr:contains(' + term + ')').each(function(i) {
				$(this).show();
				$gradeTable.find('tr').eq($(this).index() + 1).show();
			});
		} else {
			$studentTable.find('tbody tr').show();
			$gradeTable.find('tbody tr').show();
		}
	}

	$leftShadow.css('height', tableHeight + 'px');
	$rightShadow.css('height', tableHeight + 'px');
	$grades.append($leftShadow).append($rightShadow);
	setShadows(0);
	$grades.css('height', tableHeight);
	$gradeTable.bind('mousedown', startDrag);
	$element.find('tr').bind('mouseover', highlightRow);
	$search.bind('keyup', filter);
	$(window).bind('resize', updateWidths);
}




