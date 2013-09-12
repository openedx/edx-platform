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
        describe('constructor', function () {
            describe('before settings were filled in', function () {
                var element, errorMessage, frame;

                // This function will be executed before each of the it() specs
                // in this suite.
                beforeEach(function () {
                    loadFixtures('lti.html');

                    element = $('#lti_id');
                    errorMessage = element.find('.error_message');
                    form = element.find('.ltiLaunchForm');
                    frame = element.find('.ltiLaunchFrame');

                    spyOnEvent(form, 'submit');

                    LTI(element);
                });

                it(
                    'when URL setting is not filled form is not submited',
                    function () {

                    expect('submit').not.toHaveBeenTriggeredOn(form);
                });
            });

            describe('After the settings were filled in', function () {
                var element, errorMessage, frame;

                // This function will be executed before each of the it() specs
                // in this suite.
                beforeEach(function () {
                    loadFixtures('lti.html');

                    element = $('#lti_id');
                    errorMessage = element.find('.error_message');
                    form = element.find('.ltiLaunchForm');
                    frame = element.find('.ltiLaunchFrame');

                    spyOnEvent(form, 'submit');

                    // The user "fills in" the necessary settings, and the
                    // form will get an action URL.
                    form.attr('action', 'http://www.example.com/test_submit');

                    LTI(element);
                });

                it('when URL setting is filled form is submited', function () {
                    expect('submit').toHaveBeenTriggeredOn(form);
                });
            });
        });
    });
}());
