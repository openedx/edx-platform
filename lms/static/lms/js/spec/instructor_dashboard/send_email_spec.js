(function() {
    'use strict';

    describe('Bulk Email Queueing', function() {
        beforeEach(function() {
            var testBody, testSubject;
            testSubject = 'Test Subject';
            testBody = 'Hello, World! This is a test email message!';
            loadFixtures('coffee/fixtures/send_email.html');
            this.send_email = new SendEmail($('.send-email'));
            this.send_email.$subject.val(testSubject);
            this.send_email.$send_to.first().prop('checked', true);
            this.send_email.$emailEditor = {
                save: function() {
                    return {
                        'data': testBody
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
        });

        it('cannot send an email with no target', function() {
            var target, _i, _len, _ref;
            spyOn(window, 'alert');
            spyOn($, 'ajax');
            _ref = this.send_email.$send_to;
            for (_i = 0, _len = _ref.length; _i < _len; _i++) {
                target = _ref[_i];
                target.checked = false;
            }
            this.send_email.$btn_send.click();
            expect(window.alert).toHaveBeenCalledWith('Your message must have at least one target.');
            expect($.ajax).not.toHaveBeenCalled();
        });

        it('cannot send an email with no subject', function() {
            spyOn(window, 'alert');
            spyOn($, 'ajax');
            this.send_email.$subject.val('');
            this.send_email.$btn_send.click();
            expect(window.alert).toHaveBeenCalledWith('Your message must have a subject.');
            expect($.ajax).not.toHaveBeenCalled();
        });

        it('cannot send an email with no message', function() {
            spyOn(window, 'alert');
            spyOn($, 'ajax');
            this.send_email.$emailEditor = {
                save: function() {
                    return {
                        'data': ''
                    };
                }
            };
            this.send_email.$btn_send.click();
            expect(window.alert).toHaveBeenCalledWith('Your message cannot be blank.');
            expect($.ajax).not.toHaveBeenCalled();
        });

        it('can send a simple message to a single target', function() {
            spyOn($, 'ajax').and.callFake(function(params) {
                return params.success();
            });
            this.send_email.$btn_send.click();
            expect($('.msg-confirm').text()).toEqual(
                'Your email message was successfully queued for sending. ' +
                'In courses with a large number of learners, ' +
                'email messages to learners might take up to an hour to be sent.'
            );
            expect($.ajax).toHaveBeenCalledWith(this.ajax_params);
        });

        it('can send a simple message to a multiple targets', function() {
            var target, _i, _len, _ref;
            spyOn($, 'ajax').and.callFake(function(params) {
                return params.success();
            });
            this.ajax_params.data.send_to = JSON.stringify((function() {
                var _i, _len, _ref, _results;
                _ref = this.send_email.$send_to;
                _results = [];
                for (_i = 0, _len = _ref.length; _i < _len; _i++) {
                    target = _ref[_i];
                    _results.push(target.value);
                }
                return _results;
            }).call(this));
            _ref = this.send_email.$send_to;
            for (_i = 0, _len = _ref.length; _i < _len; _i++) {
                target = _ref[_i];
                target.checked = true;
            }
            this.send_email.$btn_send.click();
            expect($('.msg-confirm').text()).toEqual(
                'Your email message was successfully queued for sending. ' +
                'In courses with a large number of learners, ' +
                'email messages to learners might take up to an hour to be sent.'
            );
            expect($.ajax).toHaveBeenCalledWith(this.ajax_params);
        });

        it('can handle an error result from the bulk email api', function() {
            spyOn($, 'ajax').and.callFake(function(params) {
                return params.error();
            });
            spyOn(console, 'warn');
            this.send_email.$btn_send.click();
            expect($('.request-response-error').text()).toEqual('Error sending email.');
            expect(console.warn).toHaveBeenCalled();
        });

        it('selecting all learners disables cohort selections', function() {
            this.send_email.$send_to.filter('[value="learners"]').click();
            this.send_email.$cohort_targets.each(function() {
                expect(this.disabled).toBe(true);
            });
            this.send_email.$send_to.filter('[value="learners]').click();
            this.send_email.$cohort_targets.each(function() {
                expect(this.disabled).toBe(false);
            });
        });

        it('selected targets are listed after "send to:"', function() {
            this.send_email.$send_to.click();
            $('input[name="send_to"]:checked+label').each(function() {
                expect($('.send_to_list'.text())).toContain(this.innerText.replace(/\s*\n.*/g, ''));
            });
        });
    });
}).call(this);
