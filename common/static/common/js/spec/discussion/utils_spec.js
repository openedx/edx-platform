/* globals DiscussionSpecHelper, DiscussionUtil */
(function() {
    'use strict';
    describe('DiscussionUtil', function() {
        beforeEach(function() {
            DiscussionSpecHelper.setUpGlobals();
        });

        describe('updateWithUndo', function() {
            it('calls through to safeAjax with correct params, and reverts the model in case of failure', function() {
                var deferred, model, res, updates;
                deferred = $.Deferred();
                spyOn($, 'ajax').and.returnValue(deferred);
                spyOn(DiscussionUtil, 'safeAjax').and.callThrough();
                model = new Backbone.Model({
                    hello: false,
                    number: 42
                });
                updates = {
                    hello: 'world'
                };
                res = DiscussionUtil.updateWithUndo(model, updates, {
                    foo: 'bar'
                }, 'error message');
                expect(DiscussionUtil.safeAjax).toHaveBeenCalled();
                expect(model.attributes).toEqual({
                    hello: 'world',
                    number: 42
                });
                spyOn(DiscussionUtil, 'discussionAlert');
                DiscussionUtil.safeAjax.calls.mostRecent().args[0].error();
                expect(DiscussionUtil.discussionAlert).toHaveBeenCalledWith('Sorry', 'error message');
                deferred.reject();
                return expect(model.attributes).toEqual({
                    hello: false,
                    number: 42
                });
            });
            return it('rolls back the changes if the associated element is disabled', function() {
                var $elem, failed, model, res, updates;
                spyOn(DiscussionUtil, 'safeAjax').and.callThrough();
                model = new Backbone.Model({
                    hello: false,
                    number: 42
                });
                updates = {
                    hello: 'world'
                };
                $elem = jasmine.createSpyObj('$elem', ['prop']);
                $elem.prop.and.returnValue(true);
                res = DiscussionUtil.updateWithUndo(model, updates, {
                    foo: 'bar',
                    $elem: $elem
                }, 'error message');
                expect($elem.prop).toHaveBeenCalledWith('disabled');
                expect(DiscussionUtil.safeAjax).toHaveBeenCalled();
                expect(model.attributes).toEqual({
                    hello: false,
                    number: 42
                });
                failed = false;
                res.fail(function() {
                    failed = true;
                });
                return expect(failed).toBe(true);
            });
        });

        describe('safeAjax', function() {
            function dismissAlert() {
                $('.modal#discussion-alert').remove();
            }

            it('respects global beforeSend', function() {
                var beforeSendSpy = jasmine.createSpy();
                $.ajaxSetup({beforeSend: beforeSendSpy});

                var $elem = jasmine.createSpyObj('$elem', ['prop']);

                DiscussionUtil.safeAjax({
                    $elem: $elem,
                    url: '/',
                    type: 'GET',
                    dataType: 'json'
                }).always(function() {
                    dismissAlert();
                });
                expect($elem.prop).toHaveBeenCalledWith('disabled', true);
                expect(beforeSendSpy).toHaveBeenCalled();
            });
        });
    });
}).call(this);
