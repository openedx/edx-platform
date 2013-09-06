/**
 * File: constructor.js
 *
 * Purpose: Jasmine tests for LTI module (front-end part).
 *
 *
 * The front-end part of the LTI module is really simple. If an action
 * is set for the hidden LTI form, then it is submited, and the results are
 * redirected to an iframe.
 *
 * We will test that the form is only submited when the action is set (i.e.
 * not empty).
 *
 * Other aspects of LTI module will be covered by Python unit tests and
 * acceptance tests.
 *
 */

/*
 * "Hence that general is skilful in attack whose opponent does not know what
 * to defend; and he is skilful in defense whose opponent does not know what
 * to attack."
 *
 * ~ Sun Tzu
 */

(function () {
    describe('LTI', function () {
        var element, errorMessage, frame,
            editSettings = false;

        // This function will be executed before each of the it() specs
        // in this suite.
        beforeEach(function () {
            spyOn($.fn, 'submit').andCallThrough();

            loadFixtures('lti.html');

            element = $('#lti_id');
            errorMessage = element.find('.error_message');
            form = element.find('.ltiLaunchForm');
            frame = element.find('.ltiLaunchFrame');

            // First part of the tests will be running without the settings
            // filled in. Once we reach the describe() spec
            //
            //     "After the settings were filled in"
            //
            // the variable `editSettings` will be changed to `true`.
            if (editSettings) {
                form.attr('action', 'http://www.example.com/');
            }

            LTI(element);
        });

        describe('constructor', function () {
            describe('before settings were filled in', function () {
                it(
                    'when URL setting is filled form is not submited',
                    function () {

                    expect($.fn.submit).not.toHaveBeenCalled();
                });
            });

            describe('After the settings were filled in', function () {
                it('editSettings is disabled', function () {
                    expect(editSettings).toBe(false);

                    // Let us toggle edit settings switch. Next beforeEach()
                    // will populate element's attributes with settings.
                    editSettings = true;
                });

                it('when URL setting is filled form is submited', function () {
                    expect($.fn.submit).toHaveBeenCalled();
                });
            });
        });
    });
}());
