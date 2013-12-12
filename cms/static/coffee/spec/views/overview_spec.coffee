define ["js/views/overview", "js/views/feedback_notification", "sinon", "js/base", "date", "jquery.timepicker"],
(Overview, Notification, sinon) ->

    describe "Course Overview", ->
        beforeEach ->
            appendSetFixtures """
                              <div class="section-published-date">
                                  <span class="published-status">
                                      <strong>Will Release:</strong> 06/12/2013 at 04:00 UTC
                                  </span>
                                  <a href="#" class="edit-button" data-date="06/12/2013" data-time="04:00" data-locator="i4x://pfogg/42/chapter/d6b47f7b084f49debcaf67fe5436c8e2">Edit</a>
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
                              <section class="courseware-section branch" data-locator="a-location-goes-here">
                                  <li class="branch collapsed id-holder" data-locator="an-id-goes-here">
                                    <a href="#" class="delete-section-button"></a>
                                  </li>
                              </section>
                              """
    
            appendSetFixtures """
                              <section>
                                  <ol class="section-list">
                                      <li class="subsection-list branch" id="subsection-0" data-locator="subsection-0-id" style="margin:5px">
                                          <ol class="sortable-unit-list" id="subsection-list-0">
                                            <li class="unit" id="unit-0" data-parent="subsection-0-id" data-locator="zero-unit-id"></li>
                                          </ol>
                                      </li>
                                      <li class="subsection-list branch" id="subsection-1" data-locator="subsection-1-id" style="margin:5px">
                                          <ol class="sortable-unit-list" id="subsection-list-1">
                                              <li class="unit" id="unit-1" data-parent="subsection-1-id" data-locator="first-unit-id"></li>
                                              <li class="unit" id="unit-2" data-parent="subsection-1-id" data-locator="second-unit-id"></li>
                                              <li class="unit" id="unit-3" data-parent="subsection-1-id" data-locator="third-unit-id"></li>
                                          </ol>
                                      </li>
                                      <li class="subsection-list branch" id="subsection-2" data-locator="subsection-2-id" style="margin:5px">
                                          <ol class="sortable-unit-list" id="subsection-list-2">
                                              <li class="unit" id="unit-4" data-parent="subsection-2-id" data-locator="fourth-unit-id"></li>
                                          </ol>
                                      </li>
                                      <li class="subsection-list branch" id="subsection-3" data-locator="subsection-3-id style="margin:5px"">
                                          <ol class="sortable-unit-list" id="subsection-list-3">
                                          </ol>
                                      </li>
                                      <li class="subsection-list branch" id="subsection-4" data-locator="subsection-4-id" style="margin:5px">
                                          <ol class="sortable-unit-list" id="subsection-list-4">
                                              <li class="unit" id="unit-5" data-parent="subsection-4-id" data-locator="fifth-unit-id"></li>
                                          </ol>
                                      </li>
                                  </ol>
                              </section>
                              """
    
            spyOn(Overview, 'saveSetSectionScheduleDate').andCallThrough()
            # Have to do this here, as it normally gets bound in document.ready()
            $('a.save-button').click(Overview.saveSetSectionScheduleDate)
            $('a.delete-section-button').click(deleteSection)
            $(".edit-subsection-publish-settings .start-date").datepicker()

            @notificationSpy = spyOn(Notification.Mini.prototype, 'show').andCallThrough()
            window.analytics = jasmine.createSpyObj('analytics', ['track'])
            window.course_location_analytics = jasmine.createSpy()
            @xhr = sinon.useFakeXMLHttpRequest()
            requests = @requests = []
            @xhr.onCreate = (req) -> requests.push(req)

            Overview.overviewDragger.makeDraggable(
                '.unit',
                '.unit-drag-handle',
                '.sortable-unit-list',
                'li.branch, article.subsection-body'
            )

            Overview.overviewDragger.makeDraggable(
                '.subsection-list',
                '.subsection-drag-handle',
                '.section-list',
                'section'
            )
    
        afterEach ->
            delete window.analytics
            delete window.course_location_analytics
            @notificationSpy.reset()
    
        it "should save model when save is clicked", ->
            $('a.edit-button').click()
            $('a.save-button').click()
            expect(Overview.saveSetSectionScheduleDate).toHaveBeenCalled()

        it "should show a confirmation on save", ->
            $('a.edit-button').click()
            $('a.save-button').click()
            expect(@notificationSpy).toHaveBeenCalled()

        # Fails sporadically in Jenkins.
#        it "should delete model when delete is clicked", ->
#            $('a.delete-section-button').click()
#            $('a.action-primary').click()
#            expect(@requests[0].url).toEqual('/delete_item')

        it "should not delete model when cancel is clicked", ->
            $('a.delete-section-button').click()
            $('a.action-secondary').click()
            expect(@requests.length).toEqual(0)

        # Fails sporadically in Jenkins.
#        it "should show a confirmation on delete", ->
#            $('a.delete-section-button').click()
#            $('a.action-primary').click()
#            expect(@notificationSpy).toHaveBeenCalled()

        describe "findDestination", ->
            it "correctly finds the drop target of a drag", ->
                $ele = $('#unit-1')
                $ele.offset(
                    top: $ele.offset().top + 10, left: $ele.offset().left
                )
                destination = Overview.overviewDragger.findDestination($ele, 1)
                expect(destination.ele).toBe($('#unit-2'))
                expect(destination.attachMethod).toBe('before')

            it "can drag and drop across section boundaries, with special handling for single sibling", ->
                $ele = $('#unit-1')
                $unit4 = $('#unit-4')
                $ele.offset(
                    top: $unit4.offset().top + 8
                    left: $ele.offset().left
                )
                # Dragging down, we will insert after.
                destination = Overview.overviewDragger.findDestination($ele, 1)
                expect(destination.ele).toBe($unit4)
                expect(destination.attachMethod).toBe('after')

                # Dragging up, we will insert before.
                destination = Overview.overviewDragger.findDestination($ele, -1)
                expect(destination.ele).toBe($unit4)
                expect(destination.attachMethod).toBe('before')

                # If past the end the drop target, will attach after.
                $ele.offset(
                    top: $unit4.offset().top + $unit4.height() + 1
                    left: $ele.offset().left
                )
                destination = Overview.overviewDragger.findDestination($ele, 0)
                expect(destination.ele).toBe($unit4)
                expect(destination.attachMethod).toBe('after')

                $unit0 = $('#unit-0')
                # If before the start the drop target, will attach before.
                $ele.offset(
                    top: $unit0.offset().top - 16
                    left: $ele.offset().left
                )
                destination = Overview.overviewDragger.findDestination($ele, 0)
                expect(destination.ele).toBe($unit0)
                expect(destination.attachMethod).toBe('before')

            it """can drop before the first element, even if element being dragged is
               slightly before the first element""", ->
                $ele = $('#subsection-2')
                $ele.offset(
                    top: $('#subsection-0').offset().top - 5
                    left: $ele.offset().left
                )
                destination = Overview.overviewDragger.findDestination($ele, -1)
                expect(destination.ele).toBe($('#subsection-0'))
                expect(destination.attachMethod).toBe('before')

            it "can drag and drop across section boundaries, with special handling for last element", ->
                $ele = $('#unit-4')
                $ele.offset(
                    top: $('#unit-3').offset().bottom + 4
                    left: $ele.offset().left
                )
                destination = Overview.overviewDragger.findDestination($ele, -1)
                expect(destination.ele).toBe($('#unit-3'))
                # Dragging down up into last element, we have a fudge factor makes it easier to drag at beginning.
                expect(destination.attachMethod).toBe('after')
                # Now past the "fudge factor".
                $ele.offset(
                    top: $('#unit-3').offset().top + 4
                    left: $ele.offset().left
                )
                destination = Overview.overviewDragger.findDestination($ele, -1)
                expect(destination.ele).toBe($('#unit-3'))
                expect(destination.attachMethod).toBe('before')

            it """can drop past the last element, even if element being dragged is
               slightly before/taller then the last element""", ->
                $ele = $('#subsection-2')
                $ele.offset(
                    # Make the top 1 before the top of the last element in the list.
                    # This mimics the problem when the element being dropped is taller then then
                    # the last element in the list.
                    top: $('#subsection-4').offset().top - 1
                    left: $ele.offset().left
                )
                destination = Overview.overviewDragger.findDestination($ele, 1)
                expect(destination.ele).toBe($('#subsection-4'))
                expect(destination.attachMethod).toBe('after')

            it "can drag into an empty list", ->
                $ele = $('#unit-1')
                $ele.offset(
                    top: $('#subsection-3').offset().top + 10
                    left: $ele.offset().left
                )
                destination = Overview.overviewDragger.findDestination($ele, 1)
                expect(destination.ele).toBe($('#subsection-list-3'))
                expect(destination.attachMethod).toBe('prepend')

            it "reports a null destination on a failed drag", ->
                $ele = $('#unit-1')
                $ele.offset(
                    top: $ele.offset().top + 200, left: $ele.offset().left
                )
                destination = Overview.overviewDragger.findDestination($ele, 1)
                expect(destination).toEqual(
                    ele: null
                    attachMethod: ""
                )

            it "can drag into a collapsed list", ->
                $('#subsection-2').addClass('collapsed')
                $ele = $('#unit-2')
                $ele.offset(
                    top: $('#subsection-2').offset().top + 3
                    left: $ele.offset().left
                )
                destination = Overview.overviewDragger.findDestination($ele, 1)
                expect(destination.ele).toBe($('#subsection-list-2'))
                expect(destination.parentList).toBe($('#subsection-2'))
                expect(destination.attachMethod).toBe('prepend')

        describe "onDragStart", ->
            it "sets the dragState to its default values", ->
                expect(Overview.overviewDragger.dragState).toEqual({})
                # Call with some dummy data
                Overview.overviewDragger.onDragStart(
                    {element: $('#unit-1')},
                    null,
                    null
                )
                expect(Overview.overviewDragger.dragState).toEqual(
                    dropDestination: null,
                    attachMethod: '',
                    parentList: null,
                    lastY: 0,
                    dragDirection: 0
                )

            it "collapses expanded elements", ->
                expect($('#subsection-1')).not.toHaveClass('collapsed')
                Overview.overviewDragger.onDragStart(
                    {element: $('#subsection-1')},
                    null,
                    null
                )
                expect($('#subsection-1')).toHaveClass('collapsed')
                expect($('#subsection-1')).toHaveClass('expand-on-drop')

        describe "onDragMove", ->
            beforeEach ->
                @scrollSpy = spyOn(window, 'scrollBy').andCallThrough()

            it "adds the correct CSS class to the drop destination", ->
                $ele = $('#unit-1')
                dragY = $ele.offset().top + 10
                dragX = $ele.offset().left
                $ele.offset(
                    top: dragY, left: dragX
                )
                Overview.overviewDragger.onDragMove(
                    {element: $ele, dragPoint:
                        {y: dragY}}, '', {clientX: dragX}
                )
                expect($('#unit-2')).toHaveClass('drop-target drop-target-before')
                expect($ele).toHaveClass('valid-drop')

            it "does not add CSS class to the drop destination if out of bounds", ->
                $ele = $('#unit-1')
                dragY = $ele.offset().top + 10
                $ele.offset(
                    top: dragY, left: $ele.offset().left
                )
                Overview.overviewDragger.onDragMove(
                    {element: $ele, dragPoint:
                        {y: dragY}}, '', {clientX: $ele.offset().left - 3}
                )
                expect($('#unit-2')).not.toHaveClass('drop-target drop-target-before')
                expect($ele).not.toHaveClass('valid-drop')

            it "scrolls up if necessary", ->
                Overview.overviewDragger.onDragMove(
                    {element: $('#unit-1')}, '', {clientY: 2}
                )
                expect(@scrollSpy).toHaveBeenCalledWith(0, -10)

            it "scrolls down if necessary", ->
                Overview.overviewDragger.onDragMove(
                    {element: $('#unit-1')}, '', {clientY: (window.innerHeight - 5)}
                )
                expect(@scrollSpy).toHaveBeenCalledWith(0, 10)

        describe "onDragEnd", ->
            beforeEach ->
                @reorderSpy = spyOn(Overview.overviewDragger, 'handleReorder')

            afterEach ->
                @reorderSpy.reset()

            it "calls handleReorder on a successful drag", ->
                Overview.overviewDragger.dragState.dropDestination = $('#unit-2')
                Overview.overviewDragger.dragState.attachMethod = "before"
                Overview.overviewDragger.dragState.parentList = $('#subsection-1')
                $('#unit-1').offset(
                    top: $('#unit-1').offset().top + 10
                    left: $('#unit-1').offset().left
                )
                Overview.overviewDragger.onDragEnd(
                    {element: $('#unit-1')},
                null,
                    {clientX: $('#unit-1').offset().left}
                )
                expect(@reorderSpy).toHaveBeenCalled()

            it "clears out the drag state", ->
                Overview.overviewDragger.onDragEnd(
                    {element: $('#unit-1')},
                null,
                null
                )
                expect(Overview.overviewDragger.dragState).toEqual({})

            it "sets the element to the correct position", ->
                Overview.overviewDragger.onDragEnd(
                    {element: $('#unit-1')},
                null,
                null
                )
                # Chrome sets the CSS to 'auto', but Firefox uses '0px'.
                expect(['0px', 'auto']).toContain($('#unit-1').css('top'))
                expect(['0px', 'auto']).toContain($('#unit-1').css('left'))

            it "expands an element if it was collapsed on drag start", ->
                $('#subsection-1').addClass('collapsed')
                $('#subsection-1').addClass('expand-on-drop')
                Overview.overviewDragger.onDragEnd(
                    {element: $('#subsection-1')},
                null,
                null
                )
                expect($('#subsection-1')).not.toHaveClass('collapsed')
                expect($('#subsection-1')).not.toHaveClass('expand-on-drop')

            it "expands a collapsed element when something is dropped in it", ->
                $('#subsection-2').addClass('collapsed')
                Overview.overviewDragger.dragState.dropDestination = $('#list-2')
                Overview.overviewDragger.dragState.attachMethod = "prepend"
                Overview.overviewDragger.dragState.parentList = $('#subsection-2')
                Overview.overviewDragger.onDragEnd(
                    {element: $('#unit-1')},
                null,
                    {clientX: $('#unit-1').offset().left}
                )
                expect($('#subsection-2')).not.toHaveClass('collapsed')

        xdescribe "AJAX", ->
            beforeEach ->
                @requests = requests = []
                @xhr = sinon.useFakeXMLHttpRequest()
                @xhr.onCreate = (xhr) -> requests.push(xhr)

                @savingSpies = spyOnConstructor(Notification, "Mini",
                    ["show", "hide"])
                @savingSpies.show.andReturn(@savingSpies)
                @clock = sinon.useFakeTimers()

            afterEach ->
                @xhr.restore()
                @clock.restore()

            it "should send an update on reorder", ->
                Overview.overviewDragger.dragState.dropDestination = $('#unit-4')
                Overview.overviewDragger.dragState.attachMethod = "after"
                Overview.overviewDragger.dragState.parentList = $('#subsection-2')
                # Drag Unit 1 from Subsection 1 to the end of Subsection 2.
                $('#unit-1').offset(
                    top: $('#unit-4').offset().top + 10
                    left: $('#unit-4').offset().left
                )
                Overview.overviewDragger.onDragEnd(
                    {element: $('#unit-1')},
                    null,
                    {clientX: $('#unit-1').offset().left}
                )
                expect(@requests.length).toEqual(2)
                expect(@savingSpies.constructor).toHaveBeenCalled()
                expect(@savingSpies.show).toHaveBeenCalled()
                expect(@savingSpies.hide).not.toHaveBeenCalled()
                savingOptions = @savingSpies.constructor.mostRecentCall.args[0]
                expect(savingOptions.title).toMatch(/Saving/)
                expect($('#unit-1')).toHaveClass('was-dropped')
                # We expect 2 requests to be sent-- the first for removing Unit 1 from Subsection 1,
                # and the second for adding Unit 1 to the end of Subsection 2.
                expect(@requests[0].requestBody).toEqual('{"children":["second-unit-id","third-unit-id"]}')
                @requests[0].respond(200)
                expect(@savingSpies.hide).not.toHaveBeenCalled()
                expect(@requests[1].requestBody).toEqual('{"children":["fourth-unit-id","first-unit-id"]}')
                @requests[1].respond(200)
                expect(@savingSpies.hide).toHaveBeenCalled()
                # Class is removed in a timeout.
                @clock.tick(1001)
                expect($('#unit-1')).not.toHaveClass('was-dropped')
