class @DiscussionFilter
  @filterDrop: (e) ->
    $drop = $(e.target).parents('.topic_menu_wrapper, .browse-topic-drop-menu-wrapper')
    query = $(e.target).val()
    $items = $drop.find('a')

    if(query.length == 0)
      $items.removeClass('hidden')
      return;

    $items.addClass('hidden')
    $items.each (i) ->
      thisText = $(this).not('.unread').text()
      $(this).parents('ul').siblings('a').not('.unread').each (i) ->
        thisText = thisText  + ' ' + $(this).text();

      test = true
      terms = thisText.split(' ')

      if(thisText.toLowerCase().search(query.toLowerCase()) == -1)
        test = false

      if(test)
        $(this).removeClass('hidden')
        # show children
        $(this).parent().find('a').removeClass('hidden');
        # show parents
        $(this).parents('ul').siblings('a').removeClass('hidden');
