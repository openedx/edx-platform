(function() {

  describe('FeedbackForm', function() {
    beforeEach(function() {
      return loadFixtures('feedback_form.html');
    });
    return describe('constructor', function() {
      beforeEach(function() {
        new FeedbackForm;
        return spyOn($, 'post').andCallFake(function(url, data, callback, format) {
          return callback();
        });
      });
      it('binds to the #feedback_button', function() {
        return expect($('#feedback_button')).toHandle('click');
      });
      it('post data to /send_feedback on click', function() {
        $('#feedback_subject').val('Awesome!');
        $('#feedback_message').val('This site is really good.');
        $('#feedback_button').click();
        return expect($.postWithPrefix).toHaveBeenCalledWith('/send_feedback', {
          subject: 'Awesome!',
          message: 'This site is really good.',
          url: window.location.href
        }, jasmine.any(Function), 'json');
      });
      return it('replace the form with a thank you message', function() {
        $('#feedback_button').click();
        return expect($('#feedback_div').html()).toEqual('Feedback submitted. Thank you');
      });
    });
  });

}).call(this);
