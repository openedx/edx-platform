class @DiscussionSpecHelper
    # This is sad. We should avoid dependence on global vars.
    @setUpGlobals = ->
        DiscussionUtil.loadRoles({"Moderator": [], "Administrator": [], "Community TA": []})
        window.$$course_id = "edX/999/test"
        window.user = new DiscussionUser({username: "test_user", id: "567", upvoted_ids: []})
        DiscussionUtil.setUser(window.user)

    @makeTA = () ->
        DiscussionUtil.roleIds["Community TA"].push(parseInt(DiscussionUtil.getUser().id))

    @makeModerator = () ->
        DiscussionUtil.roleIds["Moderator"].push(parseInt(DiscussionUtil.getUser().id))

    @makeAjaxSpy = (fakeAjax) ->
        spyOn($, "ajax").andCallFake(
            (params) ->
                fakeAjax(params)
                {always: ->}
        )

    @makeEventSpy = () ->
        jasmine.createSpyObj('event', ['preventDefault', 'target'])

    @makeCourseSettings = (is_cohorted=true) ->
        new DiscussionCourseSettings(
            category_map:
                children: ['Test Topic', 'Other Topic']
                entries:
                    'Test Topic':
                        is_cohorted: is_cohorted
                        id: 'test_topic'
                    'Other Topic':
                        is_cohorted: is_cohorted
                        id: 'other_topic'
            is_cohorted: is_cohorted
        )

    @setUnderscoreFixtures = ->
        templateNames = [
            'thread', 'thread-show', 'thread-edit',
            'thread-response', 'thread-response-show', 'thread-response-edit',
            'response-comment-show', 'response-comment-edit',
            'thread-list-item', 'discussion-home', 'search-alert',
            'new-post', 'thread-type', 'new-post-menu-entry',
            'new-post-menu-category', 'topic', 'post-user-display',
            'inline-discussion', 'pagination', 'user-profile', 'profile-thread'
        ]
        templateNamesNoTrailingTemplate = [
            'forum-action-endorse', 'forum-action-answer', 'forum-action-follow',
            'forum-action-vote', 'forum-action-report', 'forum-action-pin',
            'forum-action-close', 'forum-action-edit', 'forum-action-delete',
            'forum-actions',
        ]

        for templateName in templateNames
            templateFixture = readFixtures('common/templates/discussion/' + templateName + '.underscore')
            appendSetFixtures($('<script>', { id: templateName + '-template', type: 'text/template' })
                .text(templateFixture))
        for templateName in templateNamesNoTrailingTemplate
            templateFixture = readFixtures('common/templates/discussion/' + templateName + '.underscore')
            appendSetFixtures($('<script>', { id: templateName, type: 'text/template' })
                .text(templateFixture))
        appendSetFixtures("""
            <div id="fixture-element"></div>
            <div id="discussion-container"
                data-course-name="Fake Course"
                data-user-create-comment="true"
                data-user-create-subcomment="true"
                data-read-only="false"
            ></div>
        """)
