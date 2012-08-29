var $body;
var $browse;
var $search;
var $searchField;
var $topicDrop;
var $currentBoard;
var $tooltip;
var $newPost;
var $thread;
var $sidebar;
var $sidebarWidthStyles;
var sidebarWidth;
var tooltipTimer;
var tooltipCoords;


$(document).ready(function() {
	$body = $('body');
	$browse = $('.browse-search .browse');
	$search = $('.browse-search .search');
	$searchField = $('.post-search-field');
	$topicDrop = $('.board-drop-menu');
	$currentBoard = $('.current-board');
	$tooltip = $('<div class="tooltip"></div>');
	$sidebar = $('.sidebar');
	$sidebarWidthStyles = $('<style></style>');
	$body.append($sidebarWidthStyles);

	sidebarWidth = $('.sidebar').width();

	$browse.bind('click', showTopicDrop);
	$search.bind('click', showSearch);
	$topicDrop.bind('click', setTopic);

	$('[data-tooltip]').bind({
		'mouseover': showTooltip,
		'mousemove': moveTooltip,
		'mouseout': hideTooltip,
		'click': hideTooltip
	});

	$(window).bind('resize', updateSidebarWidth);
	updateSidebarWidth();
});

function showTooltip(e) {
	var tooltipText = $(this).attr('data-tooltip');
	$tooltip.html(tooltipText);
	$body.append($tooltip);
	$(this).children().css('pointer-events', 'none');

	tooltipCoords = {
		x: e.pageX - ($tooltip.outerWidth() / 2),
		y: e.pageY - ($tooltip.outerHeight() + 15)
	};

	$tooltip.css({
		'left': tooltipCoords.x,
		'top': tooltipCoords.y
	});

	tooltipTimer = setTimeout(function() {
		$tooltip.show().css('opacity', 1);

		tooltipTimer = setTimeout(function() {
			hideTooltip();
		}, 3000);
	}, 500);
}

function moveTooltip(e) {
	tooltipCoords = {
		x: e.pageX - ($tooltip.outerWidth() / 2),
		y: e.pageY - ($tooltip.outerHeight() + 15)
	};

	$tooltip.css({
		'left': tooltipCoords.x,
		'top': tooltipCoords.y
	});
}

function hideTooltip(e) {
	$tooltip.hide().css('opacity', 0);
	clearTimeout(tooltipTimer);
}

function showBrowse(e) {
	$browse.addClass('is-open');
	$search.removeClass('is-open');
	$searchField.val('');
}

function showSearch(e) {
	$search.addClass('is-open');
	$browse.removeClass('is-open');
	setTimeout(function() {
		$searchField.focus();
	}, 200);
}

function showTopicDrop(e) {
	e.preventDefault();

	$browse.addClass('is-dropped');
	$topicDrop.show();
	$browse.unbind('click', showTopicDrop);
	$browse.bind('click', hideTopicDrop);
	setTimeout(function() {
		$body.bind('click', hideTopicDrop);
	}, 0);
}

function hideTopicDrop(e) {
	$browse.removeClass('is-dropped');
	$topicDrop.hide();
	$body.unbind('click', hideTopicDrop);
	$browse.bind('click', showTopicDrop);
}

function setTopic(e) {
	var $item = $(e.target).closest('a');
	var boardName = $item.find('.board-name').html();
	$item.parents('ul').not('.board-drop-menu').each(function(i) {
		boardName = $(this).siblings('a').find('.board-name').html() + ' / ' + boardName;
	});
	$currentBoard.html(boardName);

	var fontSize = 16;
	$currentBoard.css('font-size', '16px');

	while($currentBoard.width() > (sidebarWidth * .8) - 40) {
		fontSize--;
		if(fontSize < 11) {
			break;
		}
		$currentBoard.css('font-size', fontSize + 'px');
	}

	showBrowse();
}

function updateSidebarWidth(e) {
	sidebarWidth = $sidebar.width();
	var titleWidth = sidebarWidth - 115;
	console.log(titleWidth);
	$sidebarWidthStyles.html('.discussion-body .post-list a .title { width: ' + titleWidth + 'px !important; }');
}