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
                    'when URL setting is empty error message is shown',
                    function () {

                    expect(errorMessage).not.toHaveClass('hidden');
                });

                it('when URL setting is empty iframe is hidden', function () {
                    expect(frame).toHaveClass('hidden');
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

                it(
                    'when URL setting is filled error message is hidden',
                    function () {

                    expect(errorMessage).toHaveClass('hidden');
                });

                it('when URL setting is filled iframe is shown', function () {
                    expect(frame).not.toHaveClass('hidden');
                });
            });
        });
    });
}());
