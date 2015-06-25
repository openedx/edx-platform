# -*- coding: utf-8 -*-
describe "DiscussionThreadProfileView", ->

    beforeEach ->

        setFixtures """
        <article class="discussion-thread" id="thread_1"></article>
        <script type='text/template' id='_profile_thread'>
          <article class="discussion-article" data-id="{{id}}">
            <div class="discussion-post local">
              <div class="post-body">{{{abbreviatedBody}}}</div>
            </div>
          </article>
        </script>
        """
        @threadData = {
            id: "1",
            body: "dummy body",
            discussion: new Discussion()
            abuse_flaggers: [],
            commentable_id: 'dummy_discussion',
            votes: {up_count: "42"}
        }
        @imageTag = '<img src="https://www.google.com.pk/images/srpr/logo11w.png">'
        window.MathJax = { Hub: { Queue: -> } }

    makeView = (thread) ->
      view = new DiscussionThreadProfileView(el: $("article#thread_#{thread.id}"), model: thread)
      spyConvertMath(view)
      return view

    makeThread = (threadData) ->
      thread = new Thread(threadData)
      thread.discussion = new Discussion()
      return thread

    spyConvertMath = (view) ->
      spyOn(view, "convertMath").andCallFake( ->
          @model.set('markdownBody', @model.get('body'))
        )

    checkPostWithImages = (numberOfImages, truncatedText, threadData, imageTag) ->
      expectedHtml = '<p>'
      threadData.body = '<p>'
      testText = ''
      expectedText = ''

      if truncatedText
        testText = new Array(100).join('test ')
        expectedText = testText.substring(0, 139)+ '…'
      else
        testText = 'Test body'
        expectedText = 'Test body'

        for i in [0..numberOfImages-1]
          threadData.body = threadData.body + imageTag
          if i == 0
            expectedHtml = expectedHtml + imageTag
          else
            expectedHtml = expectedHtml + '<em>image omitted</em>'

      threadData.body = threadData.body + '<em>' + testText + '</em></p>'
      if numberOfImages > 1
        expectedHtml = expectedHtml + '<em>' + expectedText + '</em></p><p><em>Some images in this post have been omitted</em></p>'
      else
        expectedHtml = expectedHtml + '<em>' + expectedText + '</em></p>'

      view = makeView(makeThread(threadData))
      view.render()
      expect(view.$el.find(".post-body").html()).toEqual(expectedHtml)

    checkBody = (truncated, view, threadData) ->
      view.render()
      if not truncated
        expect(view.model.get("body")).toEqual(view.model.get("abbreviatedBody"))
        expect(view.$el.find(".post-body").html()).toEqual(threadData.body)
      else
        expect(view.model.get("body")).not.toEqual(view.model.get("abbreviatedBody"))
        expect(view.$el.find(".post-body").html()).not.toEqual(threadData.body)
        outputHtmlStripped = view.$el.find(".post-body").html().replace(/(<([^>]+)>)/ig,"");
        outputHtmlStripped = outputHtmlStripped.replace("Some images in this post have been omitted","")
        outputHtmlStripped = outputHtmlStripped.replace("image omitted","")
        inputHtmlStripped = threadData.body.replace(/(<([^>]+)>)/ig,"");
        expectedOutput = inputHtmlStripped.substring(0, 139)+ '…'
        expect(outputHtmlStripped).toEqual(expectedOutput)
        expect(view.$el.find(".post-body").html().indexOf("…")).toBeGreaterThan(0)

    describe "Body markdown should be correct", ->

      it "untruncated text without markdown body", ->
        @threadData.body = "Test body"
        view = makeView(makeThread(@threadData))
        checkBody(false, view, @threadData)

      it "truncated text without markdown body", ->
        @threadData.body = new Array(100).join("test ")
        view = makeView(makeThread(@threadData))
        checkBody(true, view, @threadData)

      it "untruncated text with markdown body", ->
        @threadData.body = '<p>' + @imageTag + '<em>Google top search engine</em></p>'
        view = makeView(makeThread(@threadData))
        checkBody(false, view, @threadData)

      it "truncated text with markdown body", ->
        testText = new Array(100).join("test ")
        @threadData.body = '<p>' + @imageTag + @imageTag + '<em>' + testText + '</em></p>'
        view = makeView(makeThread(@threadData))
        checkBody(true, view, @threadData)

      for numImages in [1, 2, 10]
        for truncatedText in [true, false]
          it "body with #{numImages} images and #{if truncatedText then "truncated" else "untruncated"} text", ->
            checkPostWithImages(numImages, truncatedText, @threadData, @imageTag)

      it "check the thread retrieve url", ->
        thread = makeThread(@threadData)
        expect(thread.urlFor('retrieve')).toBe('/courses/edX/999/test/discussion/forum/dummy_discussion/threads/1')
