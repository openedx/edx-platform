/*
var $gradebook;

$(document).ready(function() {
	console.log('gradebook');
});
*/




var Gradebook = function($element) {
	var _this = this;
	_this.$element = $element;
	_this.$grades = $element.find('.grade-table');
	_this.maxScroll = _this.$grades.width() - _this.$element.find('.grades').width();
	_this.body = $('body');

	_this.startDrag = function(e) {
		_this.mouseOrigin = e.pageX;
		_this.tableOrigin = _this.$grades.position().left;
		_this.body.bind('mousemove', _this.moveDrag);
		_this.body.bind('mouseup', _this.stopDrag);
	};

	_this.moveDrag = function(e) {
		var offset = e.pageX - _this.mouseOrigin;
		var targetLeft = _this.clamp(_this.tableOrigin + offset, -_this.maxScroll, 0);

		console.log(offset);

		_this.$grades.css({
			'left': targetLeft + 'px'
		})
	};

	_this.stopDrag = function(e) {
		_this.body.unbind('mousemove', _this.moveDrag);
		_this.body.unbind('mouseup', _this.stopDrag);
	};

	_this.clamp = function(val, min, max) {
	    if(val > max) return max;
	    if(val < min) return min;
	    return val;
	}

	_this.$element.bind('mousedown', _this.startDrag);
}