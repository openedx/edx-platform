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
    var element, container, form, link,
        IN_NEW_WINDOW = 'true',
        IN_IFRAME = 'false',
        EMPTY_URL = '',
        DEFAULT_URL = 'http://www.example.com',
        NEW_URL = 'http://www.example.com/some_book';

    function initialize(target, action) {
        var tempEl;

        loadFixtures('lti.html');

        element = $('.lti-wrapper');
        container = element.find('.lti');
        form = container.find('.ltiLaunchForm');

        if (target === IN_IFRAME) {
            container.data('open_in_a_new_page', 'false');
            form.attr('target', 'ltiLaunchFrame');
        }

        form.attr('action', action);

        // If we have a new proper action (non-default), we create either
        // a link that will submit the form, or an iframe that will contain
        // the answer of auto submitted form.
        if (action !== EMPTY_URL && action !== DEFAULT_URL) {
            if (target === IN_NEW_WINDOW) {
                $('<a />', {
                    href: '#',
                    class: 'link_lti_new_window'
                }).appendTo(container);

                link = container.find('.link_lti_new_window');
            } else {
                $('<iframe />', {
                    name: 'ltiLaunchFrame',
                    class: 'ltiLaunchFrame',
                    src: ''
                }).appendTo(container);
            }
        }

        spyOnEvent(form, 'submit');

        LTI(element);
    }

    describe('LTI', function () {
        describe('initialize', function () {
            describe(
                'open_in_a_new_page is "true", launch URL is empty',
                function () {

                beforeEach(function () {
                    initialize(IN_NEW_WINDOW, EMPTY_URL);
                });

                it('form is not submitted', function () {
                    expect('submit').not.toHaveBeenTriggeredOn(form);
                });
            });

            describe(
                'open_in_a_new_page is "true", launch URL is default',
                function () {

                beforeEach(function () {
                    initialize(IN_NEW_WINDOW, DEFAULT_URL);
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
                    initialize(IN_NEW_WINDOW, NEW_URL);
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
                    initialize(IN_IFRAME, EMPTY_URL);
                });

                it('form is not submitted', function () {
                    expect('submit').not.toHaveBeenTriggeredOn(form);
                });
            });

            describe(
                'open_in_a_new_page is "false", launch URL is default',
                function () {

                beforeEach(function () {
                    initialize(IN_IFRAME, DEFAULT_URL);
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
                    initialize(IN_IFRAME, NEW_URL);
                });

                it('form is submitted', function () {
                    expect('submit').toHaveBeenTriggeredOn(form);
                });
            });
        });
    });
}());
