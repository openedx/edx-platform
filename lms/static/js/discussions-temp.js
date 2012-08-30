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
var $formTopicDropBtn;
var $formTopicDropMenu;
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
	$newPost = $('.new-post-article');
	$sidebar = $('.sidebar');
	$formTopicDropBtn = $('.new-post-article .topic-drop-btn');
	$formTopicDropMenu = $('.new-post-article .topic-drop-menu');
	$sidebarWidthStyles = $('<style></style>');
	$body.append($sidebarWidthStyles);

	sidebarWidth = $('.sidebar').width();

	$browse.bind('click', showTopicDrop);
	$search.bind('click', showSearch);
	$topicDrop.bind('click', setTopic);
	$formTopicDropBtn.bind('click', showFormTopicDrop);
	$formTopicDropMenu.bind('click', setFormTopic);
	$('.new-post-btn').bind('click', newPost);

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

function newPost(e) {
	$newPost.slideDown(300);
}

function showFormTopicDrop(e) {
	$formTopicDropBtn.addClass('is-dropped');
	$formTopicDropMenu.show();
	$formTopicDropBtn.unbind('click', showFormTopicDrop);
	$formTopicDropBtn.bind('click', hideFormTopicDrop);

	setTimeout(function() {
		$body.bind('click', hideFormTopicDrop);
	}, 0);
	
}

function hideFormTopicDrop(e) {
	$formTopicDropBtn.removeClass('is-dropped');
	$formTopicDropMenu.hide();
	$body.unbind('click', hideFormTopicDrop);
	$formTopicDropBtn.unbind('click', hideFormTopicDrop);
	$formTopicDropBtn.bind('click', showFormTopicDrop);
}

function setFormTopic(e) {
	$formTopicDropBtn.removeClass('is-dropped');
	hideFormTopicDrop();

	var $item = $(e.target);
	var boardName = $item.html();
	$item.parents('ul').not('.topic-drop-menu').each(function(i) {
		boardName = $(this).siblings('a').html() + ' / ' + boardName;
	});
	$formTopicDropBtn.html(boardName + ' <span class="drop-arrow">▾</span>');
}