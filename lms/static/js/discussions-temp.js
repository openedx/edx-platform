var $body;
var $browse;
var $search;
var $searchField;
var $currentBoard;

var $newPost;
var $sidebar;
var $sidebarWidthStyles;
var $postListWrapper;
var $discussionBody;
var sidebarWidth;
var sidebarXOffset;
var scrollTop;


$(document).ready(function() {
	$body = $('body');
	//$browse = $('.browse-search .browse');
	//$search = $('.browse-search .search');
	$searchField = $('.post-search-field');
	//$topicDrop = $('.browse-topic-drop-menu-wrapper');
	$currentBoard = $('.current-board');

	$newPost = $('.new-post-article');
	$sidebar = $('.sidebar');
	$discussionBody = $('.discussion-body');
	$postListWrapper = $('.post-list-wrapper');
	// $dropFilter = $('.browse-topic-drop-search-input');
	// $topicFilter = $('.topic-drop-search-input');
	$sidebarWidthStyles = $('<style></style>');
	$body.append($sidebarWidthStyles);

	sidebarWidth = $('.sidebar').width();
	sidebarXOffset = $sidebar.offset().top;

	//$browse.bind('click', showTopicDrop);
	//$search.bind('click', showSearch);
	// $topicDrop.bind('click', setTopic);
//	$formTopicDropBtn.bind('click', showFormTopicDrop);
//	$formTopicDropMenu.bind('click', setFormTopic);

	$body.delegate('.browse-topic-drop-search-input, .form-topic-drop-search-input', 'keyup', filterDrop);
});

function filterDrop(e) {
	/*
	 * multiple queries
	 */

	// var $drop = $(e.target).parents('.form-topic-drop-menu-wrapper, .browse-topic-drop-menu-wrapper');
	// var queries = $(this).val().split(' ');
	// var $items = $drop.find('a');

	// if(queries.length == 0) {
	// 	$items.show();
	// 	return;
	// }

	// $items.hide();
	// $items.each(function(i) {
	// 	var thisText = $(this).children().not('.unread').text();
	// 	$(this).parents('ul').siblings('a').not('.unread').each(function(i) {
	// 		thisText = thisText  + ' ' + $(this).text();
	// 	});

	// 	var test = true;
	// 	var terms = thisText.split(' ');

	// 	for(var i = 0; i < queries.length; i++) {
	// 		if(thisText.toLowerCase().search(queries[i].toLowerCase()) == -1) {
	// 			test = false;
	// 		}
	// 	}

	// 	if(test) {
	// 		$(this).show();

	// 		// show children
	// 		$(this).parent().find('a').show();

	// 		// show parents
	// 		$(this).parents('ul').siblings('a').show();
	// 	}
	// });



	/*
	 * single query
	 */
	var $drop = $(e.target).parents('.topic_menu_wrapper, .browse-topic-drop-menu-wrapper');
	var query = $(this).val();
	var $items = $drop.find('a');

	if(query.length == 0) {
		$items.removeClass('hidden');
		return;
	}

	$items.addClass('hidden');
	$items.each(function(i) {
		var thisText = $(this).not('.unread').text();
		$(this).parents('ul').siblings('a').not('.unread').each(function(i) {
			thisText = thisText  + ' ' + $(this).text();
		});

		var test = true;
		var terms = thisText.split(' ');

		if(thisText.toLowerCase().search(query.toLowerCase()) == -1) {
			test = false;
		}

		if(test) {
			$(this).removeClass('hidden');

			// show children
			$(this).parent().find('a').removeClass('hidden');

			// show parents
			$(this).parents('ul').siblings('a').removeClass('hidden');
		}
	});
}
