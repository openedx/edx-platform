


var Gradebook = function($element) {
	var _this = this;
	var $element = $element;
	var $grades = $element.find('.grades');
	var $gradeTable = $element.find('.grade-table');
	var $leftShadow = $('<div class="left-shadow"></div>');
	var $rightShadow = $('<div class="right-shadow"></div>');
	var tableHeight = $gradeTable.height();
	var maxScroll = $gradeTable.width() - $element.find('.grades').width();
	var $body = $('body');
	var mouseOrigin;
	var tableOrigin;

	var startDrag = function(e) {
		mouseOrigin = e.pageX;
		tableOrigin = $gradeTable.position().left;
		$body.bind('mousemove', moveDrag);
		$body.bind('mouseup', stopDrag);
	};

	var moveDrag = function(e) {
		var offset = e.pageX - mouseOrigin;
		var targetLeft = clamp(tableOrigin + offset, -maxScroll, 0);

		$gradeTable.css({
			'left': targetLeft + 'px'
		});

		setShadows(targetLeft);
	};

	var stopDrag = function(e) {
		$body.unbind('mousemove', moveDrag);
		$body.unbind('mouseup', stopDrag);
	};

	var setShadows = function(left) {
		var padding = 30;

		if(left > -padding) {
			var percent = -left / padding;
			$leftShadow.css('opacity', percent);
		}

		if(left < -maxScroll + padding) {
			var percent = (maxScroll + left) / padding;
			$rightShadow.css('opacity', percent);
		}
	};

	var clamp = function(val, min, max) {
	    if(val > max) return max;
	    if(val < min) return min;
	    return val;
	};

	$leftShadow.css('height', tableHeight + 'px');
	$rightShadow.css('height', tableHeight + 'px');
	$grades.append($leftShadow).append($rightShadow);
	setShadows(0);
	$grades.css('height', tableHeight);
	$gradeTable.bind('mousedown', startDrag);
}