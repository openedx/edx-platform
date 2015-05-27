define(['backbone', 'jquery', 'js/verify_student/photocapture'],
    function (Backbone, $) {

        describe("Photo Verification", function () {

            beforeEach(function () {
                setFixtures('<div id="order-error" style="display: none;"></div><input type="radio" name="contribution" value="35" id="contribution-35" checked="checked"><input type="radio" id="contribution-other" name="contribution" value=""><input type="text" size="9" name="contribution-other-amt" id="contribution-other-amt" value="30"><img id="face_image" src="src="data:image/png;base64,dummy"><img id="photo_id_image" src="src="data:image/png;base64,dummy"><button id="pay_button">pay button</button>');
            });

            it('retake photo', function () {
                spyOn(window, "refereshPageMessage").andCallFake(function () {
                    return;
                });
                spyOn($, "ajax").andCallFake(function (e) {
                    e.success({"success": false});
                });
                submitToPaymentProcessing();
                expect(window.refereshPageMessage).toHaveBeenCalled();
            });

            it('successful submission', function () {
                spyOn(window, "submitForm").andCallFake(function () {
                    return;
                });
                spyOn($, "ajax").andCallFake(function (e) {
                    e.success({"success": true});
                });
                submitToPaymentProcessing();
                expect(window.submitForm).toHaveBeenCalled();
                expect($("#pay_button")).toHaveClass("is-disabled");
            });

            it('Error during process', function () {
                spyOn(window, "showSubmissionError").andCallFake(function () {
                    return;
                });
                spyOn($, "ajax").andCallFake(function (e) {
                    e.error({});
                });
                spyOn($.fn, "addClass").andCallThrough();
                spyOn($.fn, "removeClass").andCallThrough();

                submitToPaymentProcessing();
                expect(window.showSubmissionError).toHaveBeenCalled();

                // make sure the button isn't disabled
                expect($("#pay_button")).not.toHaveClass("is-disabled");

                // but also make sure that it was disabled during the ajax call
                expect($.fn.addClass).toHaveBeenCalledWith("is-disabled");
                expect($.fn.removeClass).toHaveBeenCalledWith("is-disabled");
            });

        });
    });
