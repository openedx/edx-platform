/**
 * File: constructor.js
 *
 * Purpose: Jasmine tests for LTI module (front-end part).
 *
 *
 * The front-end part of the LTI module is really simple. If an action
 * is set for the hidden LTI form, then it is submitted, and the results are
 * redirected to an iframe or to a new window (based on the
 * "open_in_a_new_page" attribute).
 *
 * We will test that the form is only submitted when the action is set (i.e.
 * not empty, and not the default one).
 *
 * Other aspects of LTI module will be covered by Python unit tests and
 * acceptance tests.
 */

/*
 * "Hence that general is skillful in attack whose opponent does not know what
 * to defend; and he is skillful in defense whose opponent does not know what
 * to attack."
 *
 * ~ Sun Tzu
 */

(function () {
    var element, form, frame, link;

    function initialize(fixture, hasLink) {
        loadFixtures(fixture);

        element = $('.lti-wrapper');
        if (hasLink) {
            link = element.find('a.link_lti_new_window');
        }
        form = element.find('.ltiLaunchForm');

        spyOnEvent(form, 'submit');

        LTI(element);
    }

    describe('LTI', function () {
        describe('initialize', function () {
            describe(
                'open_in_a_new_page is "true", launch URL is empty',
                function () {

                beforeEach(function () {
                    initialize('lti_newpage_url_empty.html');
                });

                it('form is not submitted', function () {
                    expect('submit').not.toHaveBeenTriggeredOn(form);
                });
            });

            describe(
                'open_in_a_new_page is "true", launch URL is default',
                function () {

                beforeEach(function () {
                    initialize('lti_newpage_url_default.html');
                });

                it('form is not submitted', function () {
                    expect('submit').not.toHaveBeenTriggeredOn(form);
                });
            });

            describe(
                'open_in_a_new_page is "true", launch URL is not empty, and ' +
                'not default',
                function () {

                beforeEach(function () {
                    initialize('lti_newpage_url_new.html', true);
                });

                it('form is not submitted', function () {
                    expect('submit').not.toHaveBeenTriggeredOn(form);
                });

                it('after link is clicked, form is submitted', function () {
                    link.trigger('click');

                    expect('submit').toHaveBeenTriggeredOn(form);
                });
            });

            describe(
                'open_in_a_new_page is "false", launch URL is empty',
                function () {

                beforeEach(function () {
                    initialize('lti_iframe_url_empty.html');
                });

                it('form is not submitted', function () {
                    expect('submit').not.toHaveBeenTriggeredOn(form);
                });
            });

            describe(
                'open_in_a_new_page is "false", launch URL is default',
                function () {

                beforeEach(function () {
                    initialize('lti_iframe_url_default.html');
                });

                it('form is not submitted', function () {
                    expect('submit').not.toHaveBeenTriggeredOn(form);
                });
            });

            describe(
                'open_in_a_new_page is "false", launch URL is not empty, ' +
                'and not default',
                function () {

                beforeEach(function () {
                    initialize('lti_iframe_url_new.html');
                });

                it('form is submitted', function () {
                    expect('submit').toHaveBeenTriggeredOn(form);
                });
            });
        });
    });
}());
