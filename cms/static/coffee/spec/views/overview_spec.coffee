define ["js/views/overview", "js/views/feedback_notification", "js/spec_helpers/create_sinon", "js/base", "date", "jquery.timepicker"],
(Overview, Notification, create_sinon) ->

    describe "Course Overview", ->
        beforeEach ->
            appendSetFixtures """
                              <div class="section-published-date">
                                  <span class="published-status">
                                      <strong>Release date:</strong> 06/12/2013 at 04:00 UTC
                                  </span>
                                  <a href="#" class="edit-release-date action " data-date="06/12/2013" data-time="04:00" data-locator="i4x://pfogg/42/chapter/d6b47f7b084f49debcaf67fe5436c8e2"><i class="icon-time"></i> <span class="sr">Edit section release date</span></a>
                              </div>
                              """

            appendSetFixtures """
                              <div class="wrapper wrapper-dialog wrapper-dialog-edit-sectionrelease edit-section-publish-settings" aria-describedby="dialog-edit-sectionrelease-description" aria-labelledby="dialog-edit-sectionrelease-title" aria-hidden="" role="dialog">
                                <div class="dialog confirm">
                                  <form class="edit-sectionrelease-dialog" action="#">
                                    <div class="form-content">
                                    <h2 class="title dialog-edit-sectionrelease-title">Section Release Date</h2>
                                    <p id="dialog-edit-sectionrelease-description" class="message">On the date set below, this section - <strong class="section-name"></strong> - will be released to students. Any units marked private will only be visible to admins.</p>

                                      <ul class="list-input picker datepair">
                                        <li class="field field-start-date">
                                          <label for="start_date">Release Day</label>
                                          <input class="start-date date" type="text" name="start_date" value="04/08/1990" placeholder="MM/DD/YYYY" class="date" size='15' autocomplete="off"/>
                                        </li>
                                        <li class="field field-start-time">
                                          <label for="start_time">Release Time (<abbr title="Coordinated Universal Time">UTC</abbr>)</label>
                                          <input class="start-time time" type="text" name="start_time" value="12:00" placeholder="HH:MM" class="time" size='10' autocomplete="off"/>
                                        </li>
                                      </ul>
                                    </div>
                                    <div class="actions">
                                      <h3 class="sr">Form Actions</h3>
                                    <ul>
                                    <li class="action-item">
                                      <a href="#" class="button action-primary action-save">Save</a>
                                    </li>
                                    <li class="action-item">
                                      <a href="#" class="button action-secondary action-cancel">Cancel</a>
                                    </li>
                                    </ul>
                                    </div>
                                  </form>
                                </div>
                              """

            appendSetFixtures """
                              <section class="courseware-section is-collapsible is-draggable" data-parent="a-parent-locator-goes-here" data-locator="a-location-goes-here">
                                  <li class="branch collapsed id-holder" data-locator="an-id-goes-here">
                                    <a href="#" data-tooltip="Delete this section" class="delete-section-button"><i class="icon-trash"></i> <span class="sr">Delete section</span></a>
                                  </li>
                              </section>
                              """

            spyOn(Overview, 'saveSetSectionScheduleDate').andCallThrough()
            # Have to do this here, as it normally gets bound in document.ready()
            $('a.action-save').click(Overview.saveSetSectionScheduleDate)
            $('a.delete-section-button').click(deleteSection)
            $(".edit-subsection-publish-settings .start-date").datepicker()

            @notificationSpy = spyOn(Notification.Mini.prototype, 'show').andCallThrough()
            window.analytics = jasmine.createSpyObj('analytics', ['track'])
            window.course_location_analytics = jasmine.createSpy()

        afterEach ->
            delete window.analytics
            delete window.course_location_analytics
            @notificationSpy.reset()

        it "should save model when save is clicked", ->
            $('a.edit-release-date').click()
            $('a.action-save').click()
            expect(Overview.saveSetSectionScheduleDate).toHaveBeenCalled()

        it "should show a confirmation on save", ->
            $('a.edit-release-date').click()
            $('a.action-save').click()
            expect(@notificationSpy).toHaveBeenCalled()

        # Fails sporadically in Jenkins.
#        it "should delete model when delete is clicked", ->
#            $('a.delete-section-button').click()
#            $('a.action-primary').click()
#            expect(@requests[0].url).toEqual('/delete_item')

        it "should not delete model when cancel is clicked", ->
            requests = create_sinon["requests"](this)

            $('a.delete-section-button').click()
            $('a.action-secondary').click()
            expect(requests.length).toEqual(0)

        # Fails sporadically in Jenkins.
#        it "should show a confirmation on delete", ->
#            $('a.delete-section-button').click()
#            $('a.action-primary').click()
#            expect(@notificationSpy).toHaveBeenCalled()
