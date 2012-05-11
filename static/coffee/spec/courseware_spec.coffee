describe 'Courseware', ->
  describe 'start', ->
    it 'create the navigation', ->
      spyOn(window, 'Navigation')
      Courseware.start()
      expect(window.Navigation).toHaveBeenCalled()

    it 'create the calculator', ->
      spyOn(window, 'Calculator')
      Courseware.start()
      expect(window.Calculator).toHaveBeenCalled()

    it 'creates the FeedbackForm', ->
      spyOn(window, 'FeedbackForm')
      Courseware.start()
      expect(window.FeedbackForm).toHaveBeenCalled()

    it 'binds the Logger', ->
      spyOn(Logger, 'bind')
      Courseware.start()
      expect(Logger.bind).toHaveBeenCalled()

  describe 'bind', ->
    beforeEach ->
      @courseware = new Courseware
      setFixtures """
        <div class="course-content">
          <div class="sequence"></div>
        </div>
        """

    it 'binds the content change event', ->
      @courseware.bind()
      expect($('.course-content .sequence')).toHandleWith 'contentChanged', @courseware.render

  describe 'render', ->
    beforeEach ->
      @courseware = new Courseware
      setFixtures """
        <div class="course-content">
          <div id="video_1" class="video" data-streams="1.0:abc1234"></div>
          <div id="video_2" class="video" data-streams="1.0:def5678"></div>
        </div>
        """

    it 'detect the video element and convert them', ->
      spyOn(window, 'Video')
      @courseware.render()
      expect(window.Video).toHaveBeenCalledWith('1', '1.0:abc1234')
      expect(window.Video).toHaveBeenCalledWith('2', '1.0:def5678')
