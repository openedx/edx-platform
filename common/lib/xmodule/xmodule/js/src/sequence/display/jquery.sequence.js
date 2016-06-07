var SequenceNav = function($element) {
	var _this = this;
	var $element = $element;
	var $wrapper = $element.find('.sequence-list-wrapper');
	var $list = $element.find('#sequence-list');
	var $arrows = $element.find('.sequence-nav-button');
	var maxScroll = $list.width() - $wrapper.width() + 20;
	var $leftShadow = $('<div class="left-shadow"></div>');
	var $rightShadow = $('<div class="right-shadow"></div>');
	var $body = $('body');
	var listOrigin;
	var mouseOrigin;

	var startDrag = function(e) {
		updateWidths();
		mouseOrigin = e.pageX;
		listOrigin = $list.position().left;
		$body.css('-webkit-user-select', 'none');
		$body.bind('mousemove', moveDrag);
		$body.bind('mouseup', stopDrag);
	};

	var moveDrag = function(e) {
		var offset = e.pageX - mouseOrigin;
		var targetLeft = clamp(listOrigin + offset, -maxScroll, 0);

		updateHorizontalPosition(targetLeft);

		setShadows(targetLeft);
	};

	var stopDrag = function(e) {
		$body.css('-webkit-user-select', 'auto');
		$body.unbind('mousemove', moveDrag);
		$body.unbind('mouseup', stopDrag);
	};

	var setShadows = function(left) {
		var left = left || $list.position().left;
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
		maxScroll = $list.width() - $wrapper.width() + 20;
		var targetLeft = clamp($list.position().left, -maxScroll, 0);
		updateHorizontalPosition(targetLeft);
		setShadows(targetLeft);
	};

	var updateHorizontalPosition = function(left) {
		$list.css({
			'left': left + 'px'
		});
	};

	var checkPosition = function(e) {
		var $active = $element.find('.active');
		if(!$active[0]) {
			return;
		}
		if($active.position().left + $active.width() > $wrapper.width() - $list.position().left) {
			$list.animate({
				'left': (-$active.position().left + $wrapper.width() - $active.width() - 10) + 'px'
			}, {
				step: setShadows
			});
		} else if($active.position().left < -$list.position().left) {
			$list.animate({
				'left': (-$active.position().left + 10) + 'px'
			}, {
				step: setShadows
			});
		}
	};

	$wrapper.append($leftShadow).append($rightShadow);
	setShadows(0);
	$wrapper.bind('mousedown', startDrag);
	$arrows.bind('click', checkPosition);
	$(window).bind('resize', updateWidths);
	setTimeout(function() {
		checkPosition();
	}, 200);
};
