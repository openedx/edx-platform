/*
 * decaffeinate suggestions:
 * DS102: Remove unnecessary code created because of implicit returns
 * Full docs: https://github.com/decaffeinate/decaffeinate/blob/master/docs/suggestions.md
 */
describe('FeedbackForm', function() {
  beforeEach(() => loadFixtures('coffee/fixtures/feedback_form.html'));

  return describe('constructor', function() {
    beforeEach(function() {
      new FeedbackForm;
      return spyOn($, 'postWithPrefix').and.callFake((url, data, callback, format) => callback());
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
