describe "DiscussionContentView", ->
    beforeEach ->

        setFixtures
        (
            """
            <div class="discussion-column">
            </div>
            """
        )
        
        @view = new DiscussionThreadListView()

    it 'defines the tag', ->
        expect($('#jasmine-fixtures')).toExist
        expect(@view.tagName).toBeDefined
        expect(@view.el.tagName.toLowerCase()).toBe 'div'

    it "defines the class", ->
        expect(@view).toBeDefined();

