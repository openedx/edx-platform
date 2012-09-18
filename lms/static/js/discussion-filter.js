var DiscussionFilter = DiscussionFilter || {};

DiscussionFilter.filterDrop = function (e) {
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
	var query = $(e.target).val();
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
