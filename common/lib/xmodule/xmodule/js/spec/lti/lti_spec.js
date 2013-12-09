/**
 * File: constructor.js
 *
 * Purpose: Jasmine tests for LTI module (front-end part).
 *
 *
 * Because LTI module is constructed so that all methods are available via the
 * prototype chain, many times we can test methods without having to
 * instantiate a new LTI object.
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

                    expect(lti.ltiEl).toBeDefined();
                    expect(lti.ltiEl).toExist();

                    expect(lti.formAction).toEqual(NEW_URL);
                    expect(lti.openInANewPage).toEqual(false);
                    expect(lti.ajaxUrl).toEqual(jasmine.any(String));

                    expect('submit').toHaveBeenTriggeredOn(lti.formEl);
                });

                afterEach(function () {
                    lti = undefined;
                });
            });

            describe('[in new window, new url]', function () {
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

                    expect(lti.disableOpenNewWindowBtn).toBe(false);
                });

                afterEach(function () {
                    lti = undefined;
                });
            });

            describe('[in iframe, NO new url]', function () {
                var testCases = [{
                        itDescription: 'URL is blank',
                        action: EMPTY_URL
                    }, {
                        itDescription: 'URL is default',
                        action: DEFAULT_URL
                    }];

                $.each(testCases, function (index, test) {
                    it(test.itDescription, function () {
                        var lti;

                        loadFixtures('lti.html');
                        setUpLtiElement(
                            $('.lti-wrapper'), IN_IFRAME, test.action
                        );

                        lti = new window.LTI('.lti-wrapper');

                        expect(lti.openInANewPage).not.toBeDefined();
                    });
                });
            });
        });

        describe('submitFormHandler method', function () {
            var thisObj;

            beforeEach(function () {
                thisObj = {
                    signatureIsNew: undefined,
                    getNewSignature: jasmine.createSpy('getNewSignature'),
                    formEl: {
                        submit: jasmine.createSpy('submit')
                    }
                };
            });

            it('signature is new', function () {
                thisObj.signatureIsNew = true;

                window.LTI.prototype.submitFormHandler.call(thisObj);

                expect(thisObj.formEl.submit).toHaveBeenCalled();
                expect(thisObj.signatureIsNew).toBe(false);
            });

            it('signature is old', function () {
                thisObj.signatureIsNew = false;

                window.LTI.prototype.submitFormHandler.call(thisObj);

                expect(thisObj.formEl.submit).not.toHaveBeenCalled();
                expect(thisObj.signatureIsNew).toBe(false);
                expect(thisObj.getNewSignature).toHaveBeenCalled();
            });

            afterEach(function () {
                thisObj = undefined;
            });
        });

        describe('getNewSignature method', function () {
            var lti;

            beforeEach(function () {
                loadFixtures('lti.html');
                setUpLtiElement($('.lti-wrapper'), IN_NEW_WINDOW, NEW_URL);

                spyOn($, 'postWithPrefix').andCallFake(
                    function (url, data, callback) {
                        callback({
                            input_fields: {}
                        });
                    }
                );

                lti = new window.LTI('.lti-wrapper');

                spyOn(lti, 'submitFormHandler').andCallThrough();
                lti.submitFormHandler.reset();

                spyOn(lti, 'handleAjaxUpdateSignature');
            });

            it(
                '"Open in new page" clicked twice, signature requested once',
                function () {
                    lti.newWindowBtnEl.click();
                    lti.newWindowBtnEl.click();

                    expect(lti.submitFormHandler).toHaveBeenCalled();
                    expect(lti.submitFormHandler.callCount).toBe(2);

                    expect($.postWithPrefix).toHaveBeenCalledWith(
                        lti.ajaxUrl + '/regenerate_signature',
                        {},
                        jasmine.any(Function)
                    );

                    expect(lti.disableOpenNewWindowBtn).toBe(true);

                    expect(lti.handleAjaxUpdateSignature)
                        .toHaveBeenCalledWith({
                            input_fields: {}
                        });
                }
            );

            afterEach(function () {
                lti = undefined;
            });
        });

        describe('handleAjaxUpdateSignature method', function () {
            var lti, oldInputFields, newInputFields,
                AjaxCallbackData = {};

            function fakePostWithPrefix(url, data, callback) {
                return callback(AjaxCallbackData);
            }

            beforeEach(function () {
                oldInputFields = {
                    oauth_nonce: '28347958723982798572',
                    oauth_timestamp: '2389479832',
                    oauth_signature: '89ru3289r3ry283y3r82ryr38yr'
                };

                newInputFields = {
                    oauth_nonce: 'ru3902ru239ru',
                    oauth_timestamp: '24ru309rur39r8u',
                    oauth_signature: '08923ru3082u2rur'
                };

                AjaxCallbackData.error = 0;
                AjaxCallbackData.input_fields = newInputFields;

                loadFixtures('lti.html');
                setUpLtiElement($('.lti-wrapper'), IN_NEW_WINDOW, NEW_URL);

                spyOn($, 'postWithPrefix').andCallFake(fakePostWithPrefix);

                lti = new window.LTI('.lti-wrapper');

                spyOn(lti, 'submitFormHandler').andCallThrough();
                spyOn(lti, 'handleAjaxUpdateSignature').andCallThrough();
                spyOn(lti.formEl, 'submit');
                spyOn(window.console, 'log').andCallThrough();

                lti.submitFormHandler.reset();
                lti.handleAjaxUpdateSignature.reset();
                lti.formEl.submit.reset();
                window.console.log.reset();
            });

            it('On second click form is updated, and submitted', function () {
                // Setup initial OAuth values in the form.
                lti.formEl.find("input[name='oauth_nonce']")
                    .val(oldInputFields.oauth_nonce);
                lti.formEl.find("input[name='oauth_timestamp']")
                    .val(oldInputFields.oauth_timestamp);
                lti.formEl.find("input[name='oauth_signature']")
                    .val(oldInputFields.oauth_signature);

                // First click. Signature is new. Should just submit the form.
                lti.newWindowBtnEl.click();

                // Initial OAuth values should not have changed.
                expect(lti.formEl.find("input[name='oauth_nonce']").val())
                    .toBe(oldInputFields.oauth_nonce);
                expect(lti.formEl.find("input[name='oauth_timestamp']").val())
                    .toBe(oldInputFields.oauth_timestamp);
                expect(lti.formEl.find("input[name='oauth_signature']").val())
                    .toBe(oldInputFields.oauth_signature);

                expect(lti.submitFormHandler).toHaveBeenCalled();
                expect(lti.submitFormHandler.callCount).toBe(1);

                expect(lti.handleAjaxUpdateSignature).not.toHaveBeenCalled();
                expect(lti.handleAjaxUpdateSignature.callCount).toBe(0);

                expect(lti.formEl.submit).toHaveBeenCalled();
                expect(lti.formEl.submit.callCount).toBe(1);

                lti.submitFormHandler.reset();
                lti.handleAjaxUpdateSignature.reset();
                lti.formEl.submit.reset();

                // Second click. Signature is old. Should request for a new
                // signature, and then submit the form.
                lti.newWindowBtnEl.click();

                expect(lti.submitFormHandler).toHaveBeenCalled();
                expect(lti.submitFormHandler.callCount).toBe(2);

                expect(lti.handleAjaxUpdateSignature).toHaveBeenCalled();
                expect(lti.handleAjaxUpdateSignature.callCount).toBe(1);

                expect(lti.formEl.submit).toHaveBeenCalled();
                expect(lti.formEl.submit.callCount).toBe(1);

                expect(lti.disableOpenNewWindowBtn).toBe(false);

                // The new OAuth values should be in the form.
                expect(lti.formEl.find("input[name='oauth_nonce']").val())
                    .toBe(newInputFields.oauth_nonce);
                expect(lti.formEl.find("input[name='oauth_timestamp']").val())
                    .toBe(newInputFields.oauth_timestamp);
                expect(lti.formEl.find("input[name='oauth_signature']").val())
                    .toBe(newInputFields.oauth_signature);
            });

            it('invalid response for new OAuth signature', function () {
                AjaxCallbackData.input_fields = 0;
                AjaxCallbackData.error = 'error';

                lti.newWindowBtnEl.click();

                lti.submitFormHandler.reset();
                lti.handleAjaxUpdateSignature.reset();
                window.console.log.reset();
                lti.formEl.submit.reset();

                lti.newWindowBtnEl.click();

                expect(lti.submitFormHandler).toHaveBeenCalled();
                expect(lti.submitFormHandler.callCount).toBe(1);

                expect(lti.handleAjaxUpdateSignature).toHaveBeenCalled();
                expect(lti.handleAjaxUpdateSignature.callCount).toBe(1);

                expect(window.console.log).toHaveBeenCalledWith(
                    jasmine.any(String)
                );

                expect(lti.formEl.submit).not.toHaveBeenCalled();
            });

            afterEach(function () {
                lti = undefined;
                oldInputFields = undefined;
                newInputFields = undefined;
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
