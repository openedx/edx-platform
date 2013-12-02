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
    var IN_NEW_WINDOW = 'true',
        IN_IFRAME = 'false',
        EMPTY_URL = '',
        DEFAULT_URL = 'http://www.example.com',
        NEW_URL = 'http://www.example.com/some_book';

    describe('LTI XModule', function () {
        describe('LTIConstructor method', function () {
            describe('[in iframe, new url]', function () {
                var lti;

                beforeEach(function () {
                    loadFixtures('lti.html');
                    setUpLtiElement($('.lti-wrapper'), IN_IFRAME, NEW_URL);

                    spyOnEvent(
                        $('.lti-wrapper').find('.ltiLaunchForm'), 'submit'
                    );

                    lti = new window.LTI('.lti-wrapper');
                });

                it('new LTI object contains all properties', function () {
                    expect(lti.el).toBeDefined();
                    expect(lti.el).toExist();

                    expect(lti.formEl).toBeDefined();
                    expect(lti.formEl).toExist();
                    expect(lti.formEl).toHaveAttr('action');

                    expect(lti.formAction).toEqual(NEW_URL);
                    expect(lti.openInANewPage).toEqual(false);
                    expect(lti.ajaxUrl).toEqual(jasmine.any(String));

                    expect(lti.formEl).toHandleWith(
                        'submit', lti.submitFormCatcher
                    );

                    expect('submit').toHaveBeenTriggeredOn(lti.formEl);
                });

                afterEach(function () {
                    lti = undefined;
                });
            });

            describe('in new window, new url', function () {
                var lti;

                beforeEach(function () {
                    loadFixtures('lti.html');
                    setUpLtiElement($('.lti-wrapper'), IN_NEW_WINDOW, NEW_URL);

                    lti = new window.LTI('.lti-wrapper');
                });

                it('check extra properties and values', function () {
                    expect(lti.openInANewPage).toEqual(true);
                    expect(lti.signatureIsNew).toBeTruthy();

                    expect(lti.newWindowBtnEl).toBeDefined();
                    expect(lti.newWindowBtnEl).toExist();
                    expect(lti.newWindowBtnEl).toHandleWith(
                        'click', lti.newWindowBtnClick
                    );
                });

                afterEach(function () {
                    lti = undefined;
                });
            });

            describe('[in iframe, NO new url]', function () {
                var lti;

                it('URL is blank', function () {
                    loadFixtures('lti.html');
                    setUpLtiElement($('.lti-wrapper'), IN_IFRAME, EMPTY_URL);

                    lti = new window.LTI('.lti-wrapper');

                    expect(lti.openInANewPage).not.toBeDefined();
                });

                it('URL is default', function () {
                    loadFixtures('lti.html');
                    setUpLtiElement($('.lti-wrapper'), IN_IFRAME, DEFAULT_URL);

                    lti = new window.LTI('.lti-wrapper');

                    expect(lti.openInANewPage).not.toBeDefined();
                });
            });
        });

        describe('submitFormCatcher method', function () {
            var thisObj, eventObj;

            beforeEach(function () {
                thisObj = {
                    signatureIsNew: undefined,
                    getNewSignature: jasmine.createSpy('getNewSignature')
                };

                eventObj = {
                    data: {
                        '_this': thisObj
                    },
                    preventDefault: jasmine.createSpy('preventDefault')
                };
            });

            it('signature is new', function () {
                thisObj.signatureIsNew = true;

                expect(window.LTI.prototype.submitFormCatcher(eventObj))
                    .toBe(true);
                expect(thisObj.signatureIsNew).toBe(false);
            });

            it('signature is old', function () {
                thisObj.signatureIsNew = false;

                expect(window.LTI.prototype.submitFormCatcher(eventObj))
                    .toBe(false);

                expect(thisObj.getNewSignature).toHaveBeenCalled();
                expect(eventObj.preventDefault).toHaveBeenCalled();
            });

            afterEach(function () {
                thisObj = undefined;
                eventObj = undefined;
            });
        });

        describe('newWindowBtnClick method', function () {
            var thisObj, eventObj;

            beforeEach(function () {
                thisObj = {
                    formEl: {
                        submit: jasmine.createSpy('submit')
                    }
                };

                eventObj = {
                    data: {
                        '_this': thisObj
                    },
                    preventDefault: jasmine.createSpy('preventDefault')
                };
            });

            it('signature is new', function () {
                window.LTI.prototype.newWindowBtnClick(eventObj);

                expect(thisObj.formEl.submit).toHaveBeenCalled();
            });

            afterEach(function () {
                thisObj = undefined;
                eventObj = undefined;
            });
        });
    });

    function setUpLtiElement(element, target, action) {
        var container, form;

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
            } else {
                $('<iframe />', {
                    name: 'ltiLaunchFrame',
                    class: 'ltiLaunchFrame',
                    src: ''
                }).appendTo(container);
            }
        }
    }
}());
