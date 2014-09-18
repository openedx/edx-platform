class @DiscussionFilter

  # TODO: this helper class duplicates functionality in DiscussionThreadListView.filterTopics
  # for use with a very similar category dropdown in the New Post form.  The two menus' implementations
  # should be merged into a single reusable view.

  @filterDrop: (e) ->
    $drop = $(e.target).parents('.topic-menu-wrapper')
    query = $(e.target).val()
    $items = $drop.find('.topic-menu-item')

    if(query.length == 0)
      $items.removeClass('hidden')
      return;

    $items.addClass('hidden')
    $items.each (i) ->

      path = $(this).parents(".topic-menu-item").andSelf()
      pathTitles = path.children(".topic-title").map((i, elem) -> $(elem).text()).get()
      pathText = pathTitles.join(" / ").toLowerCase()

      if query.split(" ").every((term) -> pathText.search(term.toLowerCase()) != -1)
        $(this).removeClass('hidden')
        # show children
        $(this).find('.topic-menu-item').removeClass('hidden');
        # show parents
        $(this).parents('.topic-menu-item').removeClass('hidden');
