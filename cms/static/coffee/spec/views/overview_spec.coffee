describe "Course Overview", ->

    beforeEach ->
        _.each ["/static/js/vendor/date.js", "/static/js/vendor/timepicker/jquery.timepicker.js", "/jsi18n/", "/static/js/vendor/draggabilly.pkgd.js"], (path) ->
          appendSetFixtures """
            <script type="text/javascript" src="#{path}"></script>
          """

        appendSetFixtures """
            <div class="section-published-date">
              <span class="published-status">
                <strong>Will Release:</strong> 06/12/2013 at 04:00 UTC
              </span>
              <a href="#" class="edit-button" data-date="06/12/2013" data-time="04:00" data-id="i4x://pfogg/42/chapter/d6b47f7b084f49debcaf67fe5436c8e2">Edit</a>
           </div>
        """

        appendSetFixtures """
          <div class="edit-subsection-publish-settings">
            <div class="settings">
              <h3>Section Release Date</h3>
              <div class="picker datepair">
                <div class="field field-start-date">
                  <label for="">Release Day</label>
                  <input class="start-date date" type="text" name="start_date" value="04/08/1990" placeholder="MM/DD/YYYY" class="date" size='15' autocomplete="off"/>
              </div>
              <div class="field field-start-time">
                <label for="">Release Time (<abbr title="Coordinated Universal Time">UTC</abbr>)</label>
                <input class="start-time time" type="text" name="start_time" value="12:00" placeholder="HH:MM" class="time" size='10' autocomplete="off"/>
              </div>
              <div class="description">
                <p>On the date set above, this section – <strong class="section-name"></strong> – will be released to students. Any units marked private will only be visible to admins.</p>
              </div>
            </div>
            <a href="#" class="save-button">Save</a><a href="#" class="cancel-button">Cancel</a>
          </div>
        </div>
        """

        appendSetFixtures """
          <section class="courseware-section branch" data-id="a-location-goes-here">
            <li class="branch collapsed id-holder" data-id="an-id-goes-here">
              <a href="#" class="delete-section-button"></a>
            </li>
          </section>
        """

        appendSetFixtures """
          <div class="subsection-list">
            <ol class="sortable-unit-list" id="list-1" data-id="parent-list-id-1">
              <li class="unit" id="unit-1" data-id="first-unit-id" data-parent-id="parent-list-id-1"></li>
              <li class="unit" id="unit-2" data-id="second-unit-id" data-parent-id="parent-list-id-1"></li>
              <li class="unit" id="unit-3" data-id="third-unit-id" data-parent-id="parent-list-id-1"></li>
            </ol>
          </div>
          </div class="subsection-list">
            <ol class="sortable-unit-list" id="list-2" data-id="parent-list-id-2">
              <li class="unit" id="unit-4" data-id="first-unit-id" data-parent-id="parent-list-id-2"></li>
            </ol>
          </div>
          <div class="subsection-list">
            <ol class="sortable-unit-list" id="list-3" data-id="parent-list-id-3"></ol>
          </div>
        """#"

        spyOn(window, 'saveSetSectionScheduleDate').andCallThrough()
        # Have to do this here, as it normally gets bound in document.ready()
        $('a.save-button').click(saveSetSectionScheduleDate)
        $('a.delete-section-button').click(deleteSection)
        $(".edit-subsection-publish-settings .start-date").datepicker()

        @notificationSpy = spyOn(CMS.Views.Notification.Mini.prototype, 'show').andCallThrough()
        window.analytics = jasmine.createSpyObj('analytics', ['track'])
        window.course_location_analytics = jasmine.createSpy()
        @xhr = sinon.useFakeXMLHttpRequest()
        requests = @requests = []
        @xhr.onCreate = (req) -> requests.push(req)

        CMS.Views.Draggabilly.makeDraggable(
          '.unit',
          '.unit-drag-handle',
          'ol.sortable-unit-list',
          'li.branch, article.subsection-body'
        )

    afterEach ->
        delete window.analytics
        delete window.course_location_analytics
        @notificationSpy.reset()

    it "should save model when save is clicked", ->
        $('a.edit-button').click()
        $('a.save-button').click()
        expect(saveSetSectionScheduleDate).toHaveBeenCalled()

    it "should show a confirmation on save", ->
        $('a.edit-button').click()
        $('a.save-button').click()
        expect(@notificationSpy).toHaveBeenCalled()

    it "should delete model when delete is clicked", ->
      deleteSpy = spyOn(window, '_deleteItem').andCallThrough()
      $('a.delete-section-button').click()
      $('a.action-primary').click()
      expect(deleteSpy).toHaveBeenCalled()
      expect(@requests[0].url).toEqual('/delete_item')

    it "should not delete model when cancel is clicked", ->
      deleteSpy = spyOn(window, '_deleteItem').andCallThrough()
      $('a.delete-section-button').click()
      $('a.action-secondary').click()
      expect(@requests.length).toEqual(0)

    it "should show a confirmation on delete", ->
      $('a.delete-section-button').click()
      $('a.action-primary').click()
      expect(@notificationSpy).toHaveBeenCalled()

    describe "findDestination", ->
      it "correctly finds the drop target of a drag", ->
        $ele = $('#unit-1')
        $ele.offset(
          top: $ele.offset().top + 10, left: $ele.offset().left
        )
        destination = CMS.Views.Draggabilly.findDestination($ele)
        expect(destination.ele).toBe($('#unit-2'))
        expect(destination.attachMethod).toBe('before')

      it "can drag and drop across section boundaries", ->
        $ele = $('#unit-1')
        $ele.offset(
          top: $('#unit-4').offset().top + 10
          left: $ele.offset().left
        )
        destination = CMS.Views.Draggabilly.findDestination($ele)
        expect(destination.ele).toBe($('#unit-4'))
        expect(destination.attachMethod).toBe('after')

      it "can drag into an empty list", ->
        $ele = $('#unit-1')
        $ele.offset(
          top: $('#list-3').offset().top + 10
          left: $ele.offset().left
        )
        destination = CMS.Views.Draggabilly.findDestination($ele)
        expect(destination.ele).toBe($('#list-3'))
        expect(destination.attachMethod).toBe('prepend')

      it "reports a null destination on a failed drag", ->
        $ele = $('#unit-1')
        $ele.offset(
          top: $ele.offset().top + 200, left: $ele.offset().left
        )
        destination = CMS.Views.Draggabilly.findDestination($ele)
        expect(destination).toEqual(
          ele: null
          attachMethod: ""
        )

    describe "onDragStart", ->
      it "sets the dragState to its default values", ->
        expect(CMS.Views.Draggabilly.dragState).toEqual({})
        # Call with some dummy data
        CMS.Views.Draggabilly.onDragStart(
          {element: $('#unit-1')},
          null,
          null
        )
        expect(CMS.Views.Draggabilly.dragState).toEqual(
          dropDestination: null,
          expandTimer: null,
          toExpand: null,
          attachMethod: '',
          parentList: null
        )

    describe "onDragMove", ->
      it "clears the expand timer state", ->
        timerSpy = spyOn(window, 'clearTimeout').andCallThrough()
        $ele = $('#unit-1')
        $ele.offset(
          top: $ele.offset().top + 10
          left: $ele.offset().left
        )
        CMS.Views.Draggabilly.onDragMove(
          {element: $ele},
          null,
          null
        )
        expect(timerSpy).toHaveBeenCalled()
        timerSpy.reset()

      it "adds the correct CSS class to the drop destination", ->
        $ele = $('#unit-1')
        $ele.offset(
          top: $ele.offset().top + 10, left: $ele.offset().left
        )
        CMS.Views.Draggabilly.onDragMove(
          {element: $ele},
          '',
          ''
        )
        expect($('#unit-2')).toHaveClass('drop-target drop-target-before')

    describe "onDragEnd", ->
      beforeEach ->
        @reorderSpy = spyOn(CMS.Views.Draggabilly, 'handleReorder')

      afterEach ->
        @reorderSpy.reset()

      it "calls handleReorder on a successful drag", ->
        $('#unit-1').offset(
          top: $('#unit-1').offset().top + 10
          left: $('#unit-1').offset().left
        )
        CMS.Views.Draggabilly.onDragEnd(
          {element: $('#unit-1')},
          null,
          {x: $('#unit-1').offset().left}
        )
        expect(@reorderSpy).toHaveBeenCalled()

      it "clears out the drag state", ->
        CMS.Views.Draggabilly.onDragEnd(
          {element: $('#unit-1')},
          null,
          null
        )
        expect(CMS.Views.Draggabilly.dragState).toEqual({})

      it "sets the element to the correct position", ->
        CMS.Views.Draggabilly.onDragEnd(
          {element: $('#unit-1')},
          null,
          null
        )
        # Chrome sets the CSS to 'auto', but Firefox uses '0px'.
        expect(['0px', 'auto']).toContain($('#unit-1').css('top'))
        expect(['0px', 'auto']).toContain($('#unit-1').css('left'))
