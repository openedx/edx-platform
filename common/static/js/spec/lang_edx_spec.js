/* global Language:true */
(function() {
    'use strict';

    describe('Language change test for lang-edx.js', function() {
        /* eslint-disable-next-line camelcase, no-var */
        var $lang_selector,
            deferred;

        beforeEach(function() {
            loadFixtures('js/fixtures/lang-edx-fixture.html');
            // eslint-disable-next-line camelcase
            $lang_selector = $('#settings-language-value');
            deferred = $.Deferred();
        });

        it('can spy on language selector change event', function() {
            spyOnEvent($lang_selector, 'change');
            // eslint-disable-next-line camelcase
            $lang_selector.trigger('change');
            expect('change').toHaveBeenTriggeredOn($lang_selector);
        });

        it('should make an AJAX request to the correct URL', function() {
            // eslint-disable-next-line no-undef
            spyOn($, 'ajax').and.returnValue(deferred);
            Language.init();
            // eslint-disable-next-line camelcase
            $lang_selector.trigger('change');
            expect($.ajax.calls.mostRecent().args[0].url).toEqual('/api/user/v1/preferences/test1/');
        });

        it('should make an AJAX request with correct type', function() {
            // eslint-disable-next-line no-undef
            spyOn($, 'ajax').and.returnValue(deferred);
            Language.init();
            // eslint-disable-next-line camelcase
            $lang_selector.trigger('change');
            expect($.ajax.calls.mostRecent().args[0].type).toEqual('PATCH');
        });

        it('should make an AJAX request with correct data', function() {
            // eslint-disable-next-line no-undef
            spyOn($, 'ajax').and.returnValue(deferred);
            Language.init();
            // eslint-disable-next-line camelcase
            $lang_selector.val('ar');
            // eslint-disable-next-line camelcase
            $lang_selector.trigger('change');
            expect($.ajax.calls.mostRecent().args[0].data).toEqual('{"pref-lang":"ar"}');

            // change to 'en' from 'ar'
            // eslint-disable-next-line camelcase
            $lang_selector.val('en');
            // eslint-disable-next-line camelcase
            $lang_selector.trigger('change');
            expect($.ajax.calls.mostRecent().args[0].data).toEqual('{"pref-lang":"en"}');
        });

        it('should call refresh on ajax failure', function() {
            // eslint-disable-next-line no-undef
            spyOn($, 'ajax').and.callFake(function() {
                // eslint-disable-next-line no-var
                var d = $.Deferred();
                d.reject();
                return d.promise();
            });
            Language.init();
            // eslint-disable-next-line no-undef
            spyOn(Language, 'refresh');
            // eslint-disable-next-line camelcase
            $lang_selector.trigger('change');
            expect(Language.refresh).toHaveBeenCalled();
        });
    });
}).call(this);
