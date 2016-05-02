describe 'FeedbackForm', ->
  beforeEach ->
    loadFixtures 'coffee/fixtures/feedback_form.html'

  describe 'constructor', ->
    beforeEach ->
      new FeedbackForm
      spyOn($, 'postWithPrefix').andCallFake (url, data, callback, format) ->
        callback()

    it 'binds to the #feedback_button', ->
      expect($('#feedback_button')).toHandle 'click'

    it 'post data to /send_feedback on click', ->
      $('#feedback_subject').val 'Awesome!'
      $('#feedback_message').val 'This site is really good.'
      $('#feedback_button').click()

      expect($.postWithPrefix).toHaveBeenCalledWith '/send_feedback', {
        subject: 'Awesome!'
        message: 'This site is really good.'
        url: window.location.href
      }, jasmine.any(Function), 'json'

    it 'replace the form with a thank you message', ->
      $('#feedback_button').click()

      expect($('#feedback_div').html()).toEqual 'Feedback submitted. Thank you'
