(function() {
    'use strict';
    describe('Bulk Email Queueing', function() {
        beforeEach(function() {
            var testBody, testSubject;
            testSubject = 'Test Subject';
            testBody = 'Hello, World! This is a test email message!';
            loadFixtures('../../fixtures/send_email.html');
            this.send_email = new window.SendEmail($('.send-email'));
            this.send_email.$subject.val(testSubject);
            this.send_email.$send_to.first().prop('checked', true);
            this.send_email.$emailEditor = {
                save: function() {
                    return {
                        data: testBody
                    };
                }
            };
            this.ajax_params = {
                type: 'POST',
                dataType: 'json',
                url: void 0,
                data: {
                    action: 'send',
                    send_to: JSON.stringify([this.send_email.$send_to.first().val()]),
                    subject: testSubject,
                    message: testBody
                },
                success: jasmine.any(Function),
                error: jasmine.any(Function)
            };
            return this.ajax_params;
        });
        it('cannot send an email with no target', function() {
            var target, i, len, ref;
            spyOn(window, 'alert');
            spyOn($, 'ajax');
            ref = this.send_email.$send_to;
            for (i = 0, len = ref.length; i < len; i++) {
                target = ref[i];
                target.checked = false;
            }
            this.send_email.$btn_send.click();
            expect(window.alert).toHaveBeenCalledWith('Your message must have at least one target.');
            return expect($.ajax).not.toHaveBeenCalled();
        });
        it('cannot send an email with no subject', function() {
            spyOn(window, 'alert');
            spyOn($, 'ajax');
            this.send_email.$subject.val('');
            this.send_email.$btn_send.click();
            expect(window.alert).toHaveBeenCalledWith('Your message must have a subject.');
            return expect($.ajax).not.toHaveBeenCalled();
        });
        it('cannot send an email with no message', function() {
            spyOn(window, 'alert');
            spyOn($, 'ajax');
            this.send_email.$emailEditor = {
                save: function() {
                    return {
                        data: ''
                    };
                }
            };
            this.send_email.$btn_send.click();
            expect(window.alert).toHaveBeenCalledWith('Your message cannot be blank.');
            return expect($.ajax).not.toHaveBeenCalled();
        });
        it('can send a simple message to a single target', function() {
            spyOn($, 'ajax').and.callFake(function(params) {
                return params.success();
            });
            this.send_email.$btn_send.click();
            expect($('.msg-confirm').text()).toEqual('Your email message was successfully queued for sending. In courses with a large number of learners, email messages to learners might take up to an hour to be sent.'); //  eslint-disable-line max-len
            return expect($.ajax).toHaveBeenCalledWith(this.ajax_params);
        });
        it('can send a simple message to a multiple targets', function() {
            var target, i, len, ref;
            spyOn($, 'ajax').and.callFake(function(params) {
                return params.success();
            });
            this.ajax_params.data.send_to = JSON.stringify((function() {
                var j, len1, ref1, results;
                ref1 = this.send_email.$send_to;
                results = [];
                for (j = 0, len1 = ref.length; j < len1; j++) {
                    target = ref1[j];
                    results.push(target.value);
                }
                return results;
            }).call(this));
            ref = this.send_email.$send_to;
            for (i = 0, len = ref.length; i < len; i++) {
                target = ref[i];
                target.checked = true;
            }
            this.send_email.$btn_send.click();
            expect($('.msg-confirm').text()).toEqual('Your email message was successfully queued for sending. In courses with a large number of learners, email messages to learners might take up to an hour to be sent.'); //  eslint-disable-line max-len
            return expect($.ajax).toHaveBeenCalledWith(this.ajax_params);
        });
        it('can handle an error result from the bulk email api', function() {
            spyOn($, 'ajax').and.callFake(function(params) {
                return params.error();
            });
            spyOn(console, 'warn');
            this.send_email.$btn_send.click();
            return expect($('.request-response-error').text()).toEqual('Error sending email.');
        });
        it('selecting all learners disables cohort selections', function() {
            this.send_email.$send_to.filter("[value='learners']").click();
            this.send_email.$cohort_targets.each(function() {
                return expect(this.disabled).toBe(true);
            });
            this.send_email.$send_to.filter("[value='learners']").click();
            return this.send_email.$cohort_targets.each(function() {
                return expect(this.disabled).toBe(false);
            });
        });
        return it('selected targets are listed after "send to:"', function() {
            this.send_email.$send_to.click();
            return $('input[name="send_to"]:checked+label').each(function() {
                return expect($('.send_to_list'.text())).toContain(this.innerText.replace(/\s*\n.*/g, ''));
            });
        });
    });
}).call(this);
