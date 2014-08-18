describe("Photo Verification", function() {

  beforeEach(function() {
      setFixtures('<div id="order-error" style="display: none;"></div><input type="radio" name="contribution" value="35" id="contribution-35" checked="checked"><input type="radio" id="contribution-other" name="contribution" value=""><input type="text" size="9" name="contribution-other-amt" id="contribution-other-amt" value="30"><img id="face_image" src="src="data:image/png;base64,dummy"><img id="photo_id_image" src="src="data:image/png;base64,dummy">');
  });

  it('retake photo', function() {
    spyOn(window,"refereshPageMessage").andCallFake(function(){
      return
    })
    spyOn($, "ajax").andCallFake(function(e) {
      e.success({"success":false});
    });
    submitToPaymentProcessing();
    expect(window.refereshPageMessage).toHaveBeenCalled();
  });

  it('successful submission', function() {
    spyOn(window,"submitForm").andCallFake(function(){
      return
    })
    spyOn($, "ajax").andCallFake(function(e) {
      e.success({"success":true});
    });
    submitToPaymentProcessing();
    expect(window.submitForm).toHaveBeenCalled();
  });

  it('Error during process', function() {
    spyOn(window,"showSubmissionError").andCallFake(function(){
      return
    })
    spyOn($, "ajax").andCallFake(function(e) {
      e.error({});
    });
    submitToPaymentProcessing();
    expect(window.showSubmissionError).toHaveBeenCalled();
  });

});
