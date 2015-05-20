describe 'DiscussionRouter', ->
  beforeEach ->
    DiscussionSpecHelper.setUpGlobals()
    DiscussionSpecHelper.setUnderscoreFixtures()
    appendSetFixtures("""
      <script type="text/template" id="thread-list-template">
          <div class="forum-nav-header">
              <a href="#" class="forum-nav-browse" aria-haspopup="true">
                  <i class="icon fa fa-bars"></i>
                  <span class="sr">Discussion topics; current selection is: </span>
                  <span class="forum-nav-browse-current">All Discussions</span>
                  ▾
              </a>
              <form class="forum-nav-search">
                  <label>
                      <span class="sr">Search</span>
                      <input class="forum-nav-search-input" type="text" placeholder="Search all posts">
                      <i class="icon fa fa-search"></i>
                  </label>
              </form>
          </div>
          <div class="forum-nav-browse-menu-wrapper" style="display: none">
              <form class="forum-nav-browse-filter">
                  <label>
                      <span class="sr">Filter Topics</span>
                      <input type="text" class="forum-nav-browse-filter-input" placeholder="filter topics">
                  </label>
              </form>
              <ul class="forum-nav-browse-menu">
                  <li class="forum-nav-browse-menu-item forum-nav-browse-menu-all">
                      <a href="#" class="forum-nav-browse-title">All Discussions</a>
                  </li>
                  <li class="forum-nav-browse-menu-item forum-nav-browse-menu-following">
                      <a href="#" class="forum-nav-browse-title"><i class="icon fa fa-star"></i>Posts I'm Following</a>
                  </li>
                  <li class="forum-nav-browse-menu-item">
                      <a href="#" class="forum-nav-browse-title">Parent</a>
                      <ul class="forum-nav-browse-submenu">
                          <li class="forum-nav-browse-menu-item">
                              <a href="#" class="forum-nav-browse-title">Target</a>
                              <ul class="forum-nav-browse-submenu">
                                  <li
                                      class="forum-nav-browse-menu-item"
                                      data-discussion-id="child"
                                      data-cohorted="false"
                                  >
                                      <a href="#" class="forum-nav-browse-title">Child</a>
                                  </li>
                              </ul>
                          <li
                              class="forum-nav-browse-menu-item"
                              data-discussion-id="sibling"
                              data-cohorted="false"
                          >
                              <a href="#" class="forum-nav-browse-title">Sibling</a>
                          </li>
                      </ul>
                  </li>
                  <li
                      class="forum-nav-browse-menu-item"
                      data-discussion-id="other"
                      data-cohorted="true"
                  >
                      <a href="#" class="forum-nav-browse-title">Other Category</a>
                  </li>
              </ul>
          </div>
          <div class="forum-nav-thread-list-wrapper">
              <div class="forum-nav-refine-bar">
                  <label class="forum-nav-filter-main">
                      <select class="forum-nav-filter-main-control">
                          <option value="all">Show all</option>
                          <option value="unread">Unread</option>
                          <option value="unanswered">Unanswered</option>
                          <option value="flagged">Flagged</option>
                      </select>
                  </label>
                  <% if (isCohorted && isPrivilegedUser) { %>
                  <label class="forum-nav-filter-cohort">
                      <span class="sr">Cohort:</span>
                      <select class="forum-nav-filter-cohort-control">
                          <option value="">in all cohorts</option>
                          <option value="1">Cohort1</option>
                          <option value="2">Cohort2</option>
                      </select>
                  </label>
                  <% } %>
                  <label class="forum-nav-sort">
                      <select class="forum-nav-sort-control">
                          <option value="date">by recent activity</option>
                          <option value="comments">by most activity</option>
                          <option value="votes">by most votes</option>
                      </select>
                  </label>
              </div>
          </div>
          <div class="search-alerts"></div>
          <ul class="forum-nav-thread-list"></ul>
      </script>
      """)

    @threads = [
      DiscussionViewSpecHelper.makeThreadWithProps({
        id: "1",
        title: "Thread1",
        votes: {up_count: '20'},
        pinned: true,
        comments_count: 1,
        created_at: '2013-04-03T20:08:39Z',
      }),
      DiscussionViewSpecHelper.makeThreadWithProps({
        id: "2",
        title: "Thread2",
        votes: {up_count: '42'},
        comments_count: 2,
        created_at: '2013-04-03T20:07:39Z',
      }),
      DiscussionViewSpecHelper.makeThreadWithProps({
        id: "3",
        title: "Thread3",
        votes: {up_count: '12'},
        comments_count: 3,
        created_at: '2013-04-03T20:06:39Z',
      }),
      DiscussionViewSpecHelper.makeThreadWithProps({
        id: "4",
        title: "Thread4",
        votes: {up_count: '25'},
        comments_count: 0,
        pinned: true,
        created_at: '2013-04-03T20:05:39Z',
      }),
    ]

    spyOn(DiscussionUtil, 'makeWmdEditor')
    @discussion = new Discussion(_.map(@threads, (thread_spec) -> new Thread(thread_spec)), {pages: 2, sort: 'date'})
    @course_settings = new DiscussionCourseSettings({
          "category_map": {
            "children": ["Topic", "General"],
            "entries": {
              "Topic": {"is_cohorted": false, "id": "topic"},
              "General": {"is_cohorted": false, "id": "general"}
            }
          },
          "allow_anonymous": false,
          "allow_anonymous_to_peers": false,
          "is_cohorted": true,
          "cohorts": [
            {"id": 1, "name": "Cohort1"},
            {"id": 2, "name": "Cohort2"}
          ]
        })
    @router = new DiscussionRouter({discussion: @discussion, course_settings: @course_settings})

  describe 'showThread', ->
    existingCheck = (thread_id) ->
      it "shows thread #{thread_id}, which is already in threads collection", ->
        DiscussionSpecHelper.makeAjaxSpy(() -> )
        spyOn(@router, 'renderThreadView')
        # precondition check - thread is in router's collection
        expect(@router.discussion.get(thread_id)).not.toBeUndefined()
        @router.showThread("irrelevant forum name", thread_id)
        expect($.ajax).not.toHaveBeenCalled()
        expect(@router.renderThreadView).toHaveBeenCalled()

    missingCheck = (forum_name, thread_id) ->
      it "requests thread #{thread_id} in forum #{forum_name} if not already in collection", ->

        DiscussionSpecHelper.makeAjaxSpy(
          (params) -> expect(params.url.path()).toBe(DiscussionUtil.urlFor('retrieve_single_thread', forum_name, thread_id))
        )
        spyOn(@router, 'renderThreadView')
        # precondition check - thread is in router's collection
        expect(@router.discussion.get(thread_id)).toBeUndefined()
        @router.showThread(forum_name, thread_id)
        # in this case showThread makes a hidden async ajax request - it's hard to hook inot it, so it's simpler and
        # sufficient to just schedule assertion to run as soon as possible, but not immediately
        setTimeout (() -> expect(@router.renderThreadView).toHaveBeenCalled()), 0


    existingCheck('1')
    existingCheck('2')
    existingCheck('3')
    existingCheck('4')

    missingCheck('forum1', '12')
    missingCheck('forum2', '15')
    missingCheck('forum3', '112')

