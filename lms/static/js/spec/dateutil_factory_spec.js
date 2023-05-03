define(['../dateutil_factory.js'], function(DateUtilIterator) {
    'use strict';

    describe('DateUtilFactory', function() {
        beforeEach(function() {
            setFixtures('<div class="test"></div>');
        });

        describe('stringHandler', function() {
            it('returns a complete string', function() {
                var localTimeString = 'RANDOM_STRING';
                var containerString = 'RANDOM_STRING_TWO {random_token}';
                var dateToken = 'random_token';
                var answer = 'RANDOM_STRING_TWO RANDOM_STRING';
                expect(DateUtilIterator.stringHandler(localTimeString, containerString, dateToken)).toEqual(answer);
            });
        });

        describe('transform', function() {
            var $form;

            it('localizes some times', function() {
                /* we have to generate a fake span and then test the resultant texts */
                var iterationKey = '.localized-datetime';
                var testLangs = {
                    en: 'Due Oct 14, 2016 08:00 UTC',
                    ru: 'Due 14 окт. 2016 г. 08:00 UTC',
                    ar: 'Due ١٤ أكتوبر ٢٠١٦ ٠٨:٠٠ UTC',
                    fr: 'Due 14 oct. 2016 08:00 UTC'
                };
                $form = $(
                    '<span class="subtitle-name localized-datetime" ' +
                    'data-timezone="UTC" ' +
                    'data-datetime="2016-10-14 08:00:00+00:00" ' +
                    'data-string="Due {date}"></span>'
                );
                Object.keys(testLangs).forEach(function(key) {
                    $form.attr('data-language', String(key));
                    $(document.body).append($form);

                    DateUtilIterator.transform(iterationKey);
                    expect($form.text()).toEqual(testLangs[key]);

                    $form.remove();
                });
                $form = null;
            });
        });
    });
});
