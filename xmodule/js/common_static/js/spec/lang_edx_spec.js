/* global Language:true*/
(function() {
    'use strict';
    describe('Language change test for lang-edx.js', function() {
        var $lang_selector,
            deferred;

        beforeEach(function() {
            loadFixtures('js/fixtures/lang-edx-fixture.html');
            $lang_selector = $('#settings-language-value');
            deferred = $.Deferred();
        });

        it('can spy on language selector change event', function() {
            spyOnEvent($lang_selector, 'change');
            $lang_selector.trigger('change');
            expect('change').toHaveBeenTriggeredOn($lang_selector);
        });

        it('should make an AJAX request to the correct URL', function() {
            spyOn($, 'ajax').and.returnValue(deferred);
            Language.init();
            $lang_selector.trigger('change');
            expect($.ajax.calls.mostRecent().args[0].url).toEqual('/api/user/v1/preferences/test1/');
        });

        it('should make an AJAX request with correct type', function() {
            spyOn($, 'ajax').and.returnValue(deferred);
            Language.init();
            $lang_selector.trigger('change');
            expect($.ajax.calls.mostRecent().args[0].type).toEqual('PATCH');
        });

        it('should make an AJAX request with correct data', function() {
            spyOn($, 'ajax').and.returnValue(deferred);
            Language.init();
            $lang_selector.val('ar');
            $lang_selector.trigger('change');
            expect($.ajax.calls.mostRecent().args[0].data).toEqual('{"pref-lang":"ar"}');

            // change to 'en' from 'ar'
            $lang_selector.val('en');
            $lang_selector.trigger('change');
            expect($.ajax.calls.mostRecent().args[0].data).toEqual('{"pref-lang":"en"}');
        });

        it('should call refresh on ajax failure', function() {
            spyOn($, 'ajax').and.callFake(function() {
                var d = $.Deferred();
                d.reject();
                return d.promise();
            });
            Language.init();
            spyOn(Language, 'refresh');
            $lang_selector.trigger('change');
            expect(Language.refresh).toHaveBeenCalled();
        });
    });
}).call(this);
