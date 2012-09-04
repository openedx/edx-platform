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
var $postListWrapper;
var $dropFilter;
var $topicFilter;
var sidebarWidth;
var sidebarHeight;
var sidebarHeaderHeight;
var sidebarXOffset;
var scrollTop;
var tooltipTimer;
var tooltipCoords;
var SIDEBAR_PADDING = -1;
var SIDEBAR_HEADER_HEIGHT = 87;


$(document).ready(function() {
	$body = $('body');
	//$browse = $('.browse-search .browse');
	//$search = $('.browse-search .search');
	$searchField = $('.post-search-field');
	//$topicDrop = $('.browse-topic-drop-menu-wrapper');
	$currentBoard = $('.current-board');
	$tooltip = $('<div class="tooltip"></div>');
	$newPost = $('.new-post-article');
	$sidebar = $('.sidebar');
	$postListWrapper = $('.post-list-wrapper');
	$formTopicDropBtn = $('.new-post-article .form-topic-drop-btn');
	$formTopicDropMenu = $('.new-post-article .form-topic-drop-menu-wrapper');
	// $dropFilter = $('.browse-topic-drop-search-input');
	// $topicFilter = $('.topic-drop-search-input');
	$sidebarWidthStyles = $('<style></style>');
	$body.append($sidebarWidthStyles);

	sidebarWidth = $('.sidebar').width();
	sidebarXOffset = $sidebar.offset().top;

	//$browse.bind('click', showTopicDrop);
	//$search.bind('click', showSearch);
	// $topicDrop.bind('click', setTopic);
	$formTopicDropBtn.bind('click', showFormTopicDrop);
	$formTopicDropMenu.bind('click', setFormTopic);
	$('.new-post-btn').bind('click', newPost);
	$('.new-post-cancel').bind('click', closeNewPost);

	$('[data-tooltip]').bind({
		'mouseover': showTooltip,
		'mousemove': moveTooltip,
		'mouseout': hideTooltip,
		'click': hideTooltip
	});

	//$body.delegate('.browse-topic-drop-btn', 'click', showTopicDrop);
	//$body.delegate('.browse-topic-drop-search-input', 'keyup', filterDrop);
	$body.delegate('.form-topic-drop-search-input', 'keyup', filterDrop);
	//$body.delegate('.browse-topic-drop-menu-wrapper', 'click', setTopic);

	$(window).bind('resize', updateSidebarDimensions);
	$(window).bind('scroll', updateSidebarCoordinates);
	updateSidebarCoordinates();
	updateSidebarDimensions();
});

function filterDrop(e) {
	var $drop = $(e.target).parents('.form-topic-drop-menu-wrapper, .browse-topic-drop-menu-wrapper');
	var queries = $(this).val().split(' ');
	var $items = $drop.find('a');

	if(queries.length == 0) {
		$items.show();
		return;
	}

	$items.hide();
	$items.each(function(i) {
		var thisText = $(this).children().not('.unread').text();
		$(this).parents('ul').siblings('a').not('.unread').each(function(i) {
			thisText = thisText  + ' ' + $(this).text();
		});

		var test = true;
		var terms = thisText.split(' ');

		for(var i = 0; i < queries.length; i++) {
			if(thisText.toLowerCase().search(queries[i].toLowerCase()) == -1) {
				test = false;
			}
		}

		if(test) {
			$(this).show();

			// show children
			$(this).parent().find('a').show();

			// show parents
			$(this).parents('ul').siblings('a').show();
		}
	});
}

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

	if(!$topicDrop[0]) {
		$topicDrop = $('.browse-topic-drop-menu-wrapper');
	}

	$topicDrop.show();
	$browse.unbind('click', showTopicDrop);
	$browse.bind('click', hideTopicDrop);
	setTimeout(function() {
		$body.bind('click', hideTopicDrop);
	}, 0);
}

function hideTopicDrop(e) {
	if(e.target == $('.browse-topic-drop-search-input')[0]) {
		return;
	}

	$browse.removeClass('is-dropped');
	$topicDrop.hide();
	$body.unbind('click', hideTopicDrop);
	$browse.bind('click', showTopicDrop);
}

function setTopic(e) {
	if(e.target == $('.browse-topic-drop-search-input')[0]) {
		return;
	}

	var $item = $(e.target).closest('a');
	var boardName = $item.find('.board-name').html();

	$item.parents('ul').not('.browse-topic-drop-menu').each(function(i) {
		boardName = $(this).siblings('a').find('.board-name').html() + ' / ' + boardName;
	});

	if(!$currentBoard[0]) {
		$currentBoard = $('.current-board');
	}
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

function newPost(e) {
	$newPost.slideDown(300);
}

function closeNewPost(e) {
	$newPost.slideUp(300);	
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
	if(e.target == $('.topic-drop-search-input')[0]) {
		return;
	}

	$formTopicDropBtn.removeClass('is-dropped');
	$formTopicDropMenu.hide();
	$body.unbind('click', hideFormTopicDrop);
	$formTopicDropBtn.unbind('click', hideFormTopicDrop);
	$formTopicDropBtn.bind('click', showFormTopicDrop);
}

function setFormTopic(e) {
	if(e.target == $('.topic-drop-search-input')[0]) {
		return;
	}
	$formTopicDropBtn.removeClass('is-dropped');
	hideFormTopicDrop(e);

	var $item = $(e.target);
	var boardName = $item.html();
	$item.parents('ul').not('.form-topic-drop-menu').each(function(i) {
		boardName = $(this).siblings('a').html() + ' / ' + boardName;
	});
	$formTopicDropBtn.html(boardName + ' <span class="drop-arrow">▾</span>');
}

//function updateSidebarCoordinates(e) {
//	scrollTop = $(window).scrollTop();
//	sidebarXOffset = $('.discussion-column').offset().top;
//
//	var marginTop = scrollTop + SIDEBAR_PADDING > sidebarXOffset ? scrollTop + SIDEBAR_PADDING - sidebarXOffset : 0;
//
//	var discussionColumnHeight = $('.discussion-column').height();
//	marginTop = marginTop + sidebarHeight > discussionColumnHeight ? discussionColumnHeight - sidebarHeight + 2 : marginTop;
//
//	$sidebar.css('margin-top', marginTop);
//	updateSidebarDimensions();
//}
//
//function updateSidebarDimensions(e) {
//	sidebarWidth = $sidebar.width();
//
//	var visibleHeader = sidebarXOffset - scrollTop > 0 ? sidebarXOffset - scrollTop : 0;
//	sidebarHeight = $(window).height() - (visibleHeader + SIDEBAR_PADDING * 2);
//	sidebarHeight = sidebarHeight > 500 ? sidebarHeight : 500;
//
//	var titleWidth = sidebarWidth - 115;
//
//	$sidebar.css('height', sidebarHeight + 'px');
//
//	if(!$postListWrapper[0]) {
//		$postListWrapper = $('.post-list-wrapper');
//	}
//
//	$postListWrapper.css('height', (sidebarHeight - SIDEBAR_HEADER_HEIGHT - 4) + 'px');
//	$sidebarWidthStyles.html('.discussion-body .post-list a .title { width: ' + titleWidth + 'px !important; }');
//}

function updateSidebarCoordinates(e) {
  if (!$('.sidebar').attr('data-top')){
    if ($('.sidebar').hasClass('fixed')){
      return;
    }
    var offset = $('.sidebar').offset();
    $('.sidebar').attr('data-top', offset.top);
  }
  $('.sidebar').css('width', .32 * $('.discussion-body').width() + 'px');

  scrollTop = $(window).scrollTop();
  offset = $('.sidebar').attr('data-top');

  if ((offset <= scrollTop)){
    $('.sidebar').addClass('fixed');
    $('.discussion-column').addClass('sidebar-fixed');
  }else{
    $('.sidebar').removeClass('fixed');
    $('.discussion-column').removeClass('sidebar-fixed');
  }

  discussionColumnHeight = $('.discussion-column').outerHeight();
  discussionColumnBottom = $('.discussion-column').offset().top + discussionColumnHeight;

  windowHeight = $(window).height();

  if((discussionColumnBottom - scrollTop) < windowHeight){
    //difference = minHeight - (discussionColumnBottom - scrollTop);
    //$('.sidebar').height(minHeight);
    //console.log(minHeight);
    //$('.sidebar').css('top', -difference);
    //$('.post-list-wrapper').height(minHeight - SIDEBAR_HEADER_HEIGHT - 4);
    $('.sidebar').removeClass('fixed');
    $('.discussion-column').removeClass('sidebar-fixed');
  }

	updateSidebarDimensions();
}

function updateSidebarDimensions(e) {

  discussionColumnHeight = $('.discussion-column').outerHeight();
  discussionColumnBottom = $('.discussion-column').offset().top + discussionColumnHeight;
  windowHeight = $(window).height();
  sidebarHeight = Math.min(windowHeight, discussionColumnHeight);
  $('.sidebar').height(sidebarHeight);
  $('.post-list-wrapper').height(sidebarHeight - SIDEBAR_HEADER_HEIGHT - 4);
  $('.sidebar').css('width', .32 * $('.discussion-body').width() + 'px');

  //$('.sidebar').height(discussionColumnBottom - scrollTop);
  //$('.post-list-wrapper').height(discussionColumnBottom - scrollTop - SIDEBAR_HEADER_HEIGHT - 4);

  if((discussionColumnBottom - scrollTop) < windowHeight){
    $('.sidebar').height(discussionColumnHeight);
    $('.post-list-wrapper').height(discussionColumnHeight - SIDEBAR_HEADER_HEIGHT - 4);
  }
}
