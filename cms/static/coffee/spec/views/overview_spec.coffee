describe "Course Overview", ->

    beforeEach ->
        appendSetFixtures """
            <script src="/static/js/vendor/date.js"></script>
        """

        appendSetFixtures """
            <script type="text/javascript" src="/jsi18n/"></script>
        """

        appendSetFixtures """
            <div class="section-published-date">
              <span class="published-status">
                <strong>Will Release:</strong> 06/12/2013 at 04:00 UTC
              </span>
              <a href="#" class="edit-button" "="" data-date="06/12/2013" data-time="04:00" data-id="i4x://pfogg/42/chapter/d6b47f7b084f49debcaf67fe5436c8e2">Edit</a>
           </div>
        """#"

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
        """#"

        spyOn(window, 'saveSetSectionScheduleDate').andCallThrough()
        # Have to do this here, as it normally gets bound in document.ready()
        $('a.save-button').click(saveSetSectionScheduleDate)
        @notificationSpy = spyOn(CMS.Views.Notification.Mini.prototype, 'show').andCallThrough()
        window.analytics = jasmine.createSpyObj('analytics', ['track'])
        window.course_location_analytics = jasmine.createSpy()
        sinon.useFakeXMLHttpRequest()

    afterEach ->
        delete window.analytics
        delete window.course_location_analytics

    it "should save model when save is clicked", ->
        $('a.edit-button').click()
        $('a.save-button').click()
        expect(saveSetSectionScheduleDate).toHaveBeenCalled()

    it "should show a confirmation on save", ->
        $('a.edit-button').click()
        $('a.save-button').click()
        expect(@notificationSpy).toHaveBeenCalled()
